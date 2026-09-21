from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import role_permission
from apps.bloodbanks.access import get_bank
from apps.donors.models import Donor

from . import services
from .models import Donation
from .serializers import (
    CompleteSerializer,
    DonationSerializer,
    RejectSerializer,
    ScheduleSerializer,
)

IsDonor = role_permission(Role.DONOR)
IsBank = role_permission(Role.BLOODBANK)
IsAnyParty = role_permission(Role.DONOR, Role.BLOODBANK, Role.ADMIN)
DONOR_ACTIONS = ('create', 'cancel')
BANK_ACTIONS = ('complete', 'reject')


def _api_error(exc):
    return serializers.ValidationError(exc.messages)


class DonationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DonationSerializer

    def get_permissions(self):
        if self.action in DONOR_ACTIONS:
            return [IsDonor()]
        if self.action in BANK_ACTIONS:
            return [IsBank()]
        return [IsAnyParty()]

    def get_queryset(self):
        queryset = Donation.objects.select_related('donor__user', 'bloodbank', 'blood_group')
        user = self.request.user
        if user.role == Role.DONOR:
            queryset = queryset.filter(donor__user=user)
        elif user.role == Role.BLOODBANK:
            queryset = queryset.filter(bloodbank=get_bank(user))
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def _own_donor(self):
        try:
            return Donor.objects.select_related('user', 'blood_group').get(user=self.request.user)
        except Donor.DoesNotExist:
            raise NotFound('Create your donor profile before scheduling a donation.')

    def create(self, request, *args, **kwargs):
        donor = self._own_donor()
        serializer = ScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            donation = services.schedule_donation(
                donor,
                data['bloodbank'],
                data['donation_date'],
                collection_location=data.get('collection_location', ''),
                user=request.user,
            )
        except DjangoValidationError as exc:
            raise _api_error(exc)
        return Response(self.get_serializer(donation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        donation = self.get_object()
        try:
            updated = services.cancel_donation(donation.pk, self._own_donor())
        except DjangoValidationError as exc:
            raise _api_error(exc)
        return Response(self.get_serializer(updated).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        donation = self.get_object()
        serializer = CompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.complete_donation(
                donation.pk, get_bank(request.user), request.user, serializer.validated_data['quantity']
            )
        except DjangoValidationError as exc:
            raise _api_error(exc)
        return Response(self.get_serializer(updated).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        donation = self.get_object()
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = services.reject_donation(
                donation.pk, get_bank(request.user), serializer.validated_data['reason']
            )
        except DjangoValidationError as exc:
            raise _api_error(exc)
        return Response(self.get_serializer(updated).data)
