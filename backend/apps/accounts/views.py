from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import BloodGroup, User
from .serializers import BloodGroupSerializer, UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class BloodGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BloodGroup.objects.all()
    serializer_class = BloodGroupSerializer
    permission_classes = [IsAdminUser]
