from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import IsAdminRole, IsHospital, role_permission
from apps.bloodrequests.models import BloodRequest
from apps.bloodrequests.serializers import BloodRequestSerializer
from apps.inventory.services import stock_by_blood_group, stock_by_bloodbank
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Hospital
from .serializers import AvailabilityQuerySerializer, HospitalSerializer

IsHospitalOrAdmin = role_permission(Role.HOSPITAL, Role.ADMIN)
HOSPITAL_ACTIONS = ('create', 'me', 'dashboard')
ACTIVE_STATUSES = (
    BloodRequest.Status.PENDING,
    BloodRequest.Status.APPROVED,
    BloodRequest.Status.MATCHED,
    BloodRequest.Status.PROCESSING,
)


class HospitalViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.action in HOSPITAL_ACTIONS:
            return [IsHospital()]
        if self.action == 'blood_availability':
            return [IsHospitalOrAdmin()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = Hospital.objects.select_related('user').order_by('id')
        verified = self.request.query_params.get('verified')
        if verified in ('true', 'false'):
            queryset = queryset.filter(user__is_verified=verified == 'true')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _own_profile(self):
        try:
            return Hospital.objects.select_related('user').get(user=self.request.user)
        except Hospital.DoesNotExist:
            raise NotFound('Hospital profile not found.')

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        hospital = self._own_profile()
        if request.method == 'GET':
            return Response(self.get_serializer(hospital).data)
        serializer = self.get_serializer(
            hospital, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/dashboard')
    def dashboard(self, request):
        hospital = self._own_profile()
        requests = BloodRequest.objects.filter(requester=request.user)
        counts = {status.value: 0 for status in BloodRequest.Status}
        for status in requests.values_list('status', flat=True):
            counts[status] += 1
        recent = requests.select_related('requester', 'hospital', 'blood_group', 'fulfilled_by_bloodbank')
        return Response(
            {
                'profile': self.get_serializer(hospital).data,
                'is_verified': request.user.is_verified,
                'request_counts': counts,
                'active_requests': sum(counts[s.value] for s in ACTIVE_STATUSES),
                'active_request_list': BloodRequestSerializer(
                    recent.filter(status__in=ACTIVE_STATUSES)[:5], many=True
                ).data,
                'recent_requests': BloodRequestSerializer(recent[:5], many=True).data,
                'available_blood': stock_by_blood_group(),
                'unread_notifications': Notification.objects.filter(
                    user=request.user, is_read=False
                ).count(),
            }
        )

    @action(detail=False, methods=['get'], url_path='blood-availability')
    def blood_availability(self, request):
        if request.user.role == Role.HOSPITAL and not request.user.is_verified:
            raise PermissionDenied(
                'Your hospital account must be verified by an administrator before searching blood availability.'
            )
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(
            stock_by_bloodbank(
                blood_group_id=query.validated_data.get('blood_group'),
                city=query.validated_data.get('city'),
            )
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        return self._set_verified(True)

    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        return self._set_verified(False)

    def _set_verified(self, value):
        hospital = self.get_object()
        hospital.user.is_verified = value
        hospital.user.save(update_fields=['is_verified', 'updated_at'])
        notify(
            hospital.user, 'verification',
            'Your hospital account has been verified.' if value else 'Your hospital verification was revoked.',
            related_object_type='hospital', related_object_id=hospital.pk,
        )
        return Response(self.get_serializer(hospital).data)
