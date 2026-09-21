from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole

from .models import BloodRequest
from .serializers import BloodRequestSerializer


class BloodRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BloodRequest.objects.select_related('requester', 'hospital', 'blood_group').order_by('id')
    serializer_class = BloodRequestSerializer
    permission_classes = [IsAdminRole]
