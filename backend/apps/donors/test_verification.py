from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.notifications.models import Notification
from apps.testing import make_donor, make_user

from .models import Donor


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class DonorVerificationTests(TestCase):
    def setUp(self):
        self.donor = make_donor()
        self.admin = client_for(make_user(Role.ADMIN))

    def test_admin_verifies_and_unverifies_with_notification(self):
        response = self.admin.post(f'/api/donors/{self.donor.id}/verify/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_verified'])
        self.donor.user.refresh_from_db()
        self.assertTrue(self.donor.user.is_verified)
        self.assertTrue(Notification.objects.filter(user=self.donor.user, type='verification', message__icontains='verified').exists())

        response = self.admin.post(f'/api/donors/{self.donor.id}/unverify/')
        self.assertFalse(response.json()['is_verified'])
        self.donor.user.refresh_from_db()
        self.assertFalse(self.donor.user.is_verified)

    def test_only_admin_can_verify(self):
        url = f'/api/donors/{self.donor.id}/verify/'
        self.assertEqual(APIClient().post(url).status_code, 401)
        self.assertEqual(client_for(self.donor.user).post(url).status_code, 403)
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK):
            self.assertEqual(client_for(make_user(role)).post(url).status_code, 403)
        self.donor.user.refresh_from_db()
        self.assertFalse(self.donor.user.is_verified)

    def test_unknown_donor_404(self):
        self.assertEqual(self.admin.post('/api/donors/99999/verify/').status_code, 404)

    def test_admin_list_verified_filter(self):
        verified = make_donor(user=make_user(Role.DONOR, is_verified=True))
        pending = self.admin.get('/api/donors/?verified=false').json()['results']
        self.assertEqual({d['id'] for d in pending}, {self.donor.id})
        done = self.admin.get('/api/donors/?verified=true').json()['results']
        self.assertEqual({d['id'] for d in done}, {verified.id})

    def test_verifying_a_donor_does_not_gate_anything_it_is_informational(self):
        # Donor actions (scheduling, dashboard, responding) never check is_verified.
        client = client_for(self.donor.user)
        self.assertEqual(client.get('/api/donors/me/').status_code, 200)
        self.assertEqual(client.get('/api/donors/me/dashboard/').status_code, 200)
