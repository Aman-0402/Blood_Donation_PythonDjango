from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, IsBloodBank
from apps.bloodrequests.models import BloodRequest
from apps.donations.models import Donation
from apps.inventory.models import InventoryTransaction
from apps.inventory.services import expiring_soon, stock_by_blood_group
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .access import get_bank
from .models import BloodBank
from .serializers import BloodBankSerializer

BANK_ACTIONS = ('create', 'me', 'dashboard')
DIRECTORY_FIELDS = ('id', 'name', 'city', 'address')


class BloodBankViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BloodBankSerializer

    def get_permissions(self):
        if self.action in BANK_ACTIONS:
            return [IsBloodBank()]
        if self.action == 'directory':
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = BloodBank.objects.select_related('user').order_by('id')
        verified = self.request.query_params.get('verified')
        if verified in ('true', 'false'):
            queryset = queryset.filter(user__is_verified=verified == 'true')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def directory(self, request):
        """Verified banks only, organisation details only. Any signed-in user can browse (e.g. donors picking where to donate)."""
        banks = BloodBank.objects.filter(user__is_verified=True).order_by('name')
        city = request.query_params.get('city')
        if city:
            banks = banks.filter(city__iexact=city)
        return Response(list(banks.values(*DIRECTORY_FIELDS)))

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        bank = get_bank(request.user, require_verified=False)
        if request.method == 'GET':
            return Response(self.get_serializer(bank).data)
        serializer = self.get_serializer(bank, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/dashboard')
    def dashboard(self, request):
        bank = get_bank(request.user, require_verified=False)
        transactions = InventoryTransaction.objects.filter(bloodbank=bank)

        def total(tx_type):
            return sum(transactions.filter(type=tx_type).values_list('units', flat=True))

        units_collected = total(InventoryTransaction.Type.COLLECTION)
        units_issued = -total(InventoryTransaction.Type.ISSUE)
        units_expired = -total(InventoryTransaction.Type.EXPIRED)

        donation_counts = {status.value: 0 for status in Donation.Status}
        for status in Donation.objects.filter(bloodbank=bank).values_list('status', flat=True):
            donation_counts[status] += 1
        request_counts = {status.value: 0 for status in BloodRequest.Status}
        for status in BloodRequest.objects.filter(fulfilled_by_bloodbank=bank).values_list('status', flat=True):
            request_counts[status] += 1
        open_for_fulfilment = BloodRequest.objects.filter(
            status=BloodRequest.Status.APPROVED, fulfilled_by_bloodbank__isnull=True
        ).count()
        return Response({
            'profile': self.get_serializer(bank).data,
            'stock_by_blood_group': stock_by_blood_group(bank),
            'expiring_within_7_days': expiring_soon(bank),
            'units_collected': units_collected,
            'units_issued': units_issued,
            'units_expired': units_expired,
            'donation_counts': donation_counts,
            'scheduled_donations': donation_counts['scheduled'],
            'my_request_counts': request_counts,
            'open_requests_for_fulfilment': open_for_fulfilment,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        })

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        return self._set_verified(True)

    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        return self._set_verified(False)

    def _set_verified(self, value):
        bank = self.get_object()
        bank.user.is_verified = value
        bank.user.save(update_fields=['is_verified', 'updated_at'])
        notify(
            bank.user, 'verification',
            'Your blood bank account has been verified.' if value else 'Your blood bank verification was revoked.',
            related_object_type='bloodbank', related_object_id=bank.pk,
        )
        return Response(self.get_serializer(bank).data)
