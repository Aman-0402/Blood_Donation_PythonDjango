from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Donor
from .serializers import DonorSerializer


class DonorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Donor.objects.select_related('user', 'blood_group').order_by('id')
    serializer_class = DonorSerializer
    permission_classes = [IsAdminUser]
