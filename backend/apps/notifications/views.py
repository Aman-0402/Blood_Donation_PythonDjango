from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.select_related('user')
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]
