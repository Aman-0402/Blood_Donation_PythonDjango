from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole

from .models import Hospital
from .serializers import HospitalSerializer


class HospitalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hospital.objects.select_related('user').order_by('id')
    serializer_class = HospitalSerializer
    permission_classes = [IsAdminRole]
