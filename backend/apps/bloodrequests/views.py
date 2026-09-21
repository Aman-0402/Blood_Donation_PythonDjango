from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import IsAdminRole, role_permission
from apps.bloodbanks.access import get_bank

from . import fulfillment
from .models import BloodRequest
from .serializers import (
    BloodRequestSerializer,
    RequestStatusHistorySerializer,
    StatusChangeSerializer,
)
from .workflow import OWNER_CANCELLABLE, change_status, record_creation

IsRequester = role_permission(Role.SEEKER, Role.HOSPITAL)
IsRequesterOrAdmin = role_permission(Role.SEEKER, Role.HOSPITAL, Role.ADMIN)
IsAnyRequestParty = role_permission(Role.SEEKER, Role.HOSPITAL, Role.ADMIN, Role.BLOODBANK)
IsBank = role_permission(Role.BLOODBANK)

BANK_ACTIONS = ('accept', 'release', 'dispatch_blood', 'complete')


class BloodRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BloodRequestSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsRequester()]
        if self.action == 'set_status':
            return [IsAdminRole()]
        if self.action in BANK_ACTIONS:
            return [IsBank()]
        if self.action in ('list', 'retrieve'):
            return [IsAnyRequestParty()]
        return [IsRequesterOrAdmin()]

    def get_queryset(self):
        queryset = BloodRequest.objects.select_related(
            'requester', 'hospital', 'blood_group', 'fulfilled_by_bloodbank'
        )
        user = self.request.user
        if user.role == Role.BLOODBANK:
            bank = get_bank(user)
            queryset = queryset.filter(
                Q(status=BloodRequest.Status.APPROVED, fulfilled_by_bloodbank__isnull=True)
                | Q(fulfilled_by_bloodbank=bank)
            )
        elif user.role != Role.ADMIN:
            queryset = queryset.filter(requester=user)
        params = self.request.query_params
        for field in ('status', 'urgency', 'blood_group'):
            value = params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role == Role.HOSPITAL and not request.user.is_verified:
            raise PermissionDenied(
                'Your hospital account must be verified by an administrator before requesting blood.'
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        extra = {}
        if user.role == Role.HOSPITAL:
            extra['hospital'] = user.hospital_profile
        instance = serializer.save(requester=user, **extra)
        record_creation(instance, user)

    def perform_update(self, serializer):
        if serializer.instance.status != BloodRequest.Status.PENDING:
            raise serializers.ValidationError('Only pending requests can be edited.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        if request.user.role != Role.ADMIN and instance.status not in OWNER_CANCELLABLE:
            raise serializers.ValidationError(
                f'A {instance.status} request cannot be cancelled.'
            )
        return self._transition(change_status, instance.pk, BloodRequest.Status.CANCELLED, request.user, '')

    @action(detail=True, methods=['post'], url_path='status')
    def set_status(self, request, pk=None):
        instance = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition(
            change_status,
            instance.pk,
            serializer.validated_data['status'],
            request.user,
            serializer.validated_data.get('note', ''),
        )

    @action(detail=True, methods=['get'], permission_classes=[IsRequesterOrAdmin])
    def history(self, request, pk=None):
        instance = self.get_object()
        return Response(RequestStatusHistorySerializer(instance.history.all(), many=True).data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        return self._bank_action(fulfillment.accept_request, request)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        return self._bank_action(fulfillment.release_request, request)

    @action(detail=True, methods=['post'], url_path='dispatch')
    def dispatch_blood(self, request, pk=None):
        return self._bank_action(fulfillment.dispatch_request, request)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        return self._bank_action(fulfillment.complete_request, request)

    def _bank_action(self, service, request):
        bank = get_bank(request.user)
        instance = self.get_object()
        try:
            updated = service(instance.pk, bank, request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return Response(self.get_serializer(updated).data)

    def _transition(self, service, request_id, new_status, user, note):
        try:
            updated = service(request_id, new_status, user, note)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return Response(self.get_serializer(updated).data)
