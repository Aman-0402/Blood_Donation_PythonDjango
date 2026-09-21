from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole

from .models import BloodInventory
from .serializers import BloodInventorySerializer


class BloodInventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BloodInventory.objects.select_related('bloodbank', 'blood_group').order_by('id')
    serializer_class = BloodInventorySerializer
    permission_classes = [IsAdminRole]
