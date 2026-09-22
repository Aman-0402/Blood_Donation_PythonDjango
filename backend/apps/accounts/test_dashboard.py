from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.bloodrequests.models import BloodRequest
from apps.donations.models import Donation
from apps.testing import blood_group, make_bloodbank, make_donor, make_hospital, make_inventory, make_user

URL = '/api/admin/dashboard/'


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class AdminDashboardTests(TestCase):
    def test_access_control(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK):
            self.assertEqual(client_for(make_user(role)).get(URL).status_code, 403)
        self.assertEqual(client_for(make_user(Role.ADMIN)).get(URL).status_code, 200)

    def test_counts_are_accurate(self):
        make_donor()
        make_donor()
        verified_hospital = make_hospital(user=make_user(Role.HOSPITAL, is_verified=True))
        make_hospital()
        bank = make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True))
        seeker = make_user(Role.SEEKER)
        BloodRequest.objects.create(
            requester=seeker, patient_name='P', blood_group=blood_group('A+'),
            units_required=1, city='X', location='X', status=BloodRequest.Status.PENDING,
        )
        BloodRequest.objects.create(
            requester=seeker, patient_name='P2', blood_group=blood_group('A+'),
            units_required=1, city='X', location='X', status=BloodRequest.Status.COMPLETED,
        )
        Donation.objects.create(
            donor=make_donor(), bloodbank=bank, blood_group=blood_group('A+'),
            donation_date='2026-01-01', status=Donation.Status.COMPLETED,
        )
        make_inventory(bank, 'A+', units=5)

        body = client_for(make_user(Role.ADMIN)).get(URL).json()
        self.assertEqual(body['total_donors'], 3)
        self.assertEqual(body['total_hospitals'], 2)
        self.assertEqual(body['verified_hospitals'], 1)
        self.assertEqual(body['total_bloodbanks'], 1)
        self.assertEqual(body['verified_bloodbanks'], 1)
        self.assertEqual(body['pending_requests'], 1)
        self.assertEqual(body['completed_requests'], 1)
        self.assertEqual(body['request_counts']['pending'], 1)
        self.assertEqual(body['donation_counts']['completed'], 1)
        stock = {r['blood_group_name']: r['units_available'] for r in body['blood_inventory']}
        self.assertEqual(stock['A+'], 5)
        self.assertEqual(len(body['blood_inventory']), 8)
        self.assertIn('admin', body['users_by_role'])
        self.assertEqual(body['users_by_role']['admin'], 1)
