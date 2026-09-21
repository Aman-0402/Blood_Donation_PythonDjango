from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import role_permission
from apps.bloodbanks.access import get_bank

from . import services
from .models import BloodInventory, InventoryTransaction
from .serializers import (
    AdjustSerializer,
    BloodInventorySerializer,
    CollectionSerializer,
    InventoryTransactionSerializer,
    IssueSerializer,
)

IsBankOrAdmin = role_permission(Role.BLOODBANK, Role.ADMIN)
IsBank = role_permission(Role.BLOODBANK)
BANK_WRITE_ACTIONS = ('create', 'issue', 'expire', 'adjust')


def _as_api_error(exc):
    return serializers.ValidationError(exc.messages)


class InventoryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BloodInventorySerializer

    def get_permissions(self):
        if self.action in BANK_WRITE_ACTIONS:
            return [IsBank()]
        return [IsBankOrAdmin()]

    def _scoped(self, queryset):
        user = self.request.user
        if user.role == Role.ADMIN:
            return queryset
        return queryset.filter(bloodbank=get_bank(user, require_verified=False))

    def get_queryset(self):
        queryset = self._scoped(BloodInventory.objects.select_related('bloodbank', 'blood_group'))
        params = self.request.query_params
        for field in ('status', 'blood_group'):
            if params.get(field):
                queryset = queryset.filter(**{field: params[field]})
        return queryset

    def create(self, request, *args, **kwargs):
        bank = get_bank(request.user)
        serializer = CollectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            batch = services.record_collection(
                bank, data['blood_group'], data['units'],
                collection_date=data.get('collection_date'),
                expiry_date=data.get('expiry_date'),
                user=request.user,
                note=data.get('note', ''),
            )
        except DjangoValidationError as exc:
            raise _as_api_error(exc)
        return Response(self.get_serializer(batch).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def issue(self, request):
        bank = get_bank(request.user)
        serializer = IssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            services.issue_units(
                bank, data['blood_group'], data['units'], user=request.user, note=data.get('note', '')
            )
        except DjangoValidationError as exc:
            raise _as_api_error(exc)
        return Response({'issued': data['units'], 'blood_group': data['blood_group'].name})

    @action(detail=False, methods=['post'])
    def expire(self, request):
        bank = get_bank(request.user)
        return Response({'expired_units': services.expire_stock(bank, user=request.user)})

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        bank = get_bank(request.user)
        batch_id = self.get_object().pk
        serializer = AdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch = services.adjust_batch(
                batch_id, serializer.validated_data['delta'], serializer.validated_data['reason'],
                bloodbank=bank, user=request.user,
            )
        except DjangoValidationError as exc:
            raise _as_api_error(exc)
        return Response(self.get_serializer(batch).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        bank = None if user.role == Role.ADMIN else get_bank(user, require_verified=False)
        expiring = services.expiring_soon(bank) if bank else {}
        rows = services.stock_by_blood_group(bank)
        for row in rows:
            row['expiring_within_7_days'] = expiring.get(row['blood_group'], 0)
        return Response(rows)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        queryset = self._scoped(
            InventoryTransaction.objects.select_related('bloodbank', 'blood_group', 'created_by')
        )
        params = request.query_params
        for field in ('type', 'blood_group'):
            if params.get(field):
                queryset = queryset.filter(**{field: params[field]})
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(InventoryTransactionSerializer(page, many=True).data)
