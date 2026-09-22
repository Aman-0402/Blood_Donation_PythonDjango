from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import blood_group, make_hospital, make_user

from .models import BloodRequest

Status = BloodRequest.Status
URL = '/api/requests/dashboard/'


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def make_request(requester, **kwargs):
    data = dict(requester=requester, patient_name='P', blood_group=blood_group('A+'), units_required=1, city='X', location='X')
    data.update(kwargs)
    return BloodRequest.objects.create(**data)


class SeekerDashboardTests(TestCase):
    def test_only_seekers(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
        for role in (Role.DONOR, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN):
            self.assertEqual(client_for(make_user(role)).get(URL).status_code, 403)

    def test_counts_scoped_to_own_requests(self):
        seeker = make_user(Role.SEEKER)
        other = make_user(Role.SEEKER)
        make_request(seeker, status=Status.PENDING)
        make_request(seeker, status=Status.APPROVED)
        make_request(seeker, status=Status.COMPLETED)
        make_request(other, status=Status.PENDING)
        body = client_for(seeker).get(URL).json()
        self.assertEqual(body['request_counts']['pending'], 1)
        self.assertEqual(body['request_counts']['approved'], 1)
        self.assertEqual(body['active_requests'], 2)
        self.assertEqual(len(body['recent_requests']), 3)

    def test_hospital_role_uses_its_own_dashboard_not_this_one(self):
        hospital = make_hospital(user=make_user(Role.HOSPITAL, is_verified=True))
        self.assertEqual(client_for(hospital.user).get(URL).status_code, 403)
