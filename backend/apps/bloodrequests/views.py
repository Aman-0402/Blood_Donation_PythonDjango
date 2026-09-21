from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import BloodRequest
from .serializers import BloodRequestSerializer


class BloodRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BloodRequest.objects.select_related('requester', 'hospital', 'blood_group').order_by('id')
    serializer_class = BloodRequestSerializer
    permission_classes = [IsAdminUser]
