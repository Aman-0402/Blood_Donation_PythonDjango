from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import BloodBank
from .serializers import BloodBankSerializer


class BloodBankViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BloodBank.objects.select_related('user').order_by('id')
    serializer_class = BloodBankSerializer
    permission_classes = [IsAdminUser]
