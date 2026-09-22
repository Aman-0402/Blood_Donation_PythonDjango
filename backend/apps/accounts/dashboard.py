from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bloodbanks.models import BloodBank
from apps.bloodrequests.models import BloodRequest
from apps.donations.models import Donation
from apps.donors.models import Donor
from apps.hospitals.models import Hospital
from apps.inventory.services import stock_by_blood_group

from .models import Role, User
from .permissions import IsAdminRole


class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        request_counts = {status.value: 0 for status in BloodRequest.Status}
        for status in BloodRequest.objects.values_list('status', flat=True):
            request_counts[status] += 1
        donation_counts = {status.value: 0 for status in Donation.Status}
        for status in Donation.objects.values_list('status', flat=True):
            donation_counts[status] += 1
        return Response({
            'total_users': User.objects.count(),
            'users_by_role': {
                role.value: User.objects.filter(role=role).count() for role in Role
            },
            'total_donors': Donor.objects.count(),
            'total_hospitals': Hospital.objects.count(),
            'verified_hospitals': Hospital.objects.filter(user__is_verified=True).count(),
            'total_bloodbanks': BloodBank.objects.count(),
            'verified_bloodbanks': BloodBank.objects.filter(user__is_verified=True).count(),
            'request_counts': request_counts,
            'pending_requests': request_counts['pending'],
            'completed_requests': request_counts['completed'],
            'donation_counts': donation_counts,
            'blood_inventory': stock_by_blood_group(),
        })
