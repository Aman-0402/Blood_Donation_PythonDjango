from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import IsAdminRole

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'mark_read', 'mark_all_read', 'unread_count'):
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = Notification.objects.select_related('user')
        user = self.request.user
        if user.role != Role.ADMIN:
            queryset = queryset.filter(user=user)
        is_read = self.request.query_params.get('is_read')
        if is_read in ('true', 'false'):
            queryset = queryset.filter(is_read=is_read == 'true')
        return queryset

    def _own(self, request):
        return Notification.objects.filter(user=request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        return Response({'count': self._own(request).filter(is_read=False).count()})

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        instance = self._own(request).filter(pk=pk).first()
        if instance is None:
            raise NotFound('Notification not found.')
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        updated = self._own(request).filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})
