from rest_framework import viewsets
from apps.accounts.permissions import IsAdminRole

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.select_related('user')
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminRole]
