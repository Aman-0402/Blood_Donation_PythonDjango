from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, IsDonor
from apps.donations.models import Donation
from apps.donations.serializers import DonationSerializer
from apps.notifications.models import Notification

from .models import Donor
from .serializers import DonorSerializer

DONOR_ACTIONS = ('create', 'me', 'my_donations', 'dashboard')


class DonorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Donor.objects.select_related('user', 'blood_group').order_by('id')
    serializer_class = DonorSerializer

    def get_permissions(self):
        if self.action in DONOR_ACTIONS:
            return [IsDonor()]
        return [IsAdminRole()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _own_profile(self):
        try:
            return Donor.objects.select_related('user', 'blood_group').get(user=self.request.user)
        except Donor.DoesNotExist:
            raise NotFound('Donor profile not found.')

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        donor = self._own_profile()
        if request.method == 'GET':
            return Response(self.get_serializer(donor).data)
        serializer = self.get_serializer(
            donor, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/donations')
    def my_donations(self, request):
        donor = self._own_profile()
        donations = donor.donations.select_related('bloodbank', 'blood_group').order_by(
            '-donation_date', '-id'
        )
        page = self.paginate_queryset(donations)
        if page is not None:
            return self.get_paginated_response(DonationSerializer(page, many=True).data)
        return Response(DonationSerializer(donations, many=True).data)

    @action(detail=False, methods=['get'], url_path='me/dashboard')
    def dashboard(self, request):
        donor = self._own_profile()
        profile = self.get_serializer(donor).data
        donations = donor.donations.select_related('bloodbank', 'blood_group')
        return Response(
            {
                'profile': profile,
                'is_available': donor.is_available,
                'is_eligible': profile['is_eligible'],
                'next_eligible_date': profile['next_eligible_date'],
                'total_donations': donations.filter(status=Donation.Status.COMPLETED).count(),
                'scheduled_donations': donations.filter(status=Donation.Status.SCHEDULED).count(),
                'recent_donations': DonationSerializer(
                    donations.order_by('-donation_date', '-id')[:5], many=True
                ).data,
                'unread_notifications': Notification.objects.filter(
                    user=request.user, is_read=False
                ).count(),
            }
        )
