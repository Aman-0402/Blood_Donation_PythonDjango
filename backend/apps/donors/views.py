from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, IsDonor
from apps.bloodrequests import matching
from apps.bloodrequests.models import DonorResponse
from apps.bloodrequests.serializers import DonorRequestSerializer, RespondSerializer
from apps.donations.models import Donation
from apps.donations.serializers import DonationSerializer
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Donor
from .serializers import DonorSerializer

DONOR_ACTIONS = ('create', 'me', 'my_donations', 'dashboard', 'my_requests', 'respond')


class DonorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DonorSerializer

    def get_permissions(self):
        if self.action in DONOR_ACTIONS:
            return [IsDonor()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = Donor.objects.select_related('user', 'blood_group').order_by('id')
        verified = self.request.query_params.get('verified')
        if verified in ('true', 'false'):
            queryset = queryset.filter(user__is_verified=verified == 'true')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        return self._set_verified(True)

    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        return self._set_verified(False)

    def _set_verified(self, value):
        donor = self.get_object()
        donor.user.is_verified = value
        donor.user.save(update_fields=['is_verified', 'updated_at'])
        notify(
            donor.user, 'verification',
            'Your donor account has been verified.' if value else 'Your donor verification was revoked.',
            related_object_type='donor', related_object_id=donor.pk,
        )
        return Response(self.get_serializer(donor).data)

    def _own_profile(self):
        try:
            return Donor.objects.select_related('user', 'blood_group').get(user=self.request.user)
        except Donor.DoesNotExist:
            raise NotFound('Donor profile not found.')

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        donor = self._own_profile()
        if request.method == 'GET':
            return Response(self.get_serializer(donor).data)
        serializer = self.get_serializer(
            donor, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/donations')
    def my_donations(self, request):
        donor = self._own_profile()
        donations = donor.donations.select_related('bloodbank', 'blood_group').order_by(
            '-donation_date', '-id'
        )
        page = self.paginate_queryset(donations)
        if page is not None:
            return self.get_paginated_response(DonationSerializer(page, many=True).data)
        return Response(DonationSerializer(donations, many=True).data)

    @action(detail=False, methods=['get'], url_path='me/dashboard')
    def dashboard(self, request):
        donor = self._own_profile()
        profile = self.get_serializer(donor).data
        donations = donor.donations.select_related('bloodbank', 'blood_group')
        return Response(
            {
                'profile': profile,
                'is_available': donor.is_available,
                'is_eligible': profile['is_eligible'],
                'next_eligible_date': profile['next_eligible_date'],
                'total_donations': donations.filter(status=Donation.Status.COMPLETED).count(),
                'scheduled_donations': donations.filter(status=Donation.Status.SCHEDULED).count(),
                'recent_donations': DonationSerializer(
                    donations.order_by('-donation_date', '-id')[:5], many=True
                ).data,
                'unread_notifications': Notification.objects.filter(
                    user=request.user, is_read=False
                ).count(),
                'matching_requests': matching.open_requests_for_donor(donor).count(),
            }
        )

    @action(detail=False, methods=['get'], url_path='me/requests')
    def my_requests(self, request):
        """Open requests in the donor's city that their blood group can serve. No patient or requester details."""
        donor = self._own_profile()
        queryset = matching.open_requests_for_donor(donor)
        responses = dict(DonorResponse.objects.filter(donor=donor).values_list('request_id', 'answer'))
        page = self.paginate_queryset(queryset)
        serializer = DonorRequestSerializer(page, many=True, context={'responses': responses})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], url_path=r'me/requests/(?P<request_id>\d+)/respond')
    def respond(self, request, request_id=None):
        """Accepting shares the donor's name and phone with the requester (and only with them)."""
        donor = self._own_profile()
        body = RespondSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            response = matching.respond_to_request(donor, int(request_id), body.validated_data['answer'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return Response({'request': response.request_id, 'answer': response.answer})
