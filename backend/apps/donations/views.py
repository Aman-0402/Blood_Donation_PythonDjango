from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole

from .models import Donation
from .serializers import DonationSerializer


class DonationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Donation.objects.select_related('donor', 'bloodbank', 'blood_group').order_by('id')
    serializer_class = DonationSerializer
    permission_classes = [IsAdminRole]
