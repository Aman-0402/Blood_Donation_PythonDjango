from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, IsBloodBank

from .access import get_bank
from .models import BloodBank
from .serializers import BloodBankSerializer

BANK_ACTIONS = ('create', 'me')
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
        return Response(self.get_serializer(bank).data)
