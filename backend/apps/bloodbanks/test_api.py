from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import make_bloodbank, make_user

from .models import BloodBank


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def profile(**overrides):
    data = {'name': 'Red Cross Bank', 'city': 'Pune', 'address': '1 Donor Rd', 'license_number': 'BB-100'}
    data.update(overrides)
    return data


class BloodBankProfileTests(TestCase):
    def setUp(self):
        self.user = make_user(Role.BLOODBANK)
        self.client = client_for(self.user)

    def test_role_gating(self):
        self.assertEqual(APIClient().post('/api/bloodbanks/', profile(), format='json').status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL, Role.ADMIN):
            with self.subTest(role=role):
                self.assertEqual(client_for(make_user(role)).post('/api/bloodbanks/', profile(), format='json').status_code, 403)

    def test_create_and_me(self):
        self.assertEqual(self.client.get('/api/bloodbanks/me/').status_code, 404)
        response = self.client.post('/api/bloodbanks/', profile(), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()['is_verified'])
        self.assertEqual(BloodBank.objects.get().user, self.user)
        self.assertEqual(self.client.get('/api/bloodbanks/me/').json()['name'], 'Red Cross Bank')

    def test_duplicate_profile_and_license_rejected(self):
        self.client.post('/api/bloodbanks/', profile(), format='json')
        self.assertEqual(self.client.post('/api/bloodbanks/', profile(license_number='X'), format='json').status_code, 400)
        other = client_for(make_user(Role.BLOODBANK))
        self.assertEqual(other.post('/api/bloodbanks/', profile(), format='json').status_code, 400)

    def test_validation(self):
        for name, data in {
            'no name': profile(name=''), 'no city': profile(city=''),
            'no license': profile(license_number=''), 'blank license': profile(license_number='  '),
        }.items():
            with self.subTest(name):
                self.assertEqual(self.client.post('/api/bloodbanks/', data, format='json').status_code, 400)

    def test_cannot_spoof_owner_or_verification(self):
        other = make_user(Role.BLOODBANK)
        self.client.post('/api/bloodbanks/', profile(user=other.id, is_verified=True), format='json')
        self.assertEqual(BloodBank.objects.get().user, self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_update_me(self):
        self.client.post('/api/bloodbanks/', profile(), format='json')
        response = self.client.patch('/api/bloodbanks/me/', {'city': 'Delhi'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BloodBank.objects.get().city, 'Delhi')


class BloodBankVerificationTests(TestCase):
    def setUp(self):
        self.bank = make_bloodbank()
        self.admin = client_for(make_user(Role.ADMIN))

    def test_admin_verifies_and_unverifies(self):
        response = self.admin.post(f'/api/bloodbanks/{self.bank.id}/verify/')
        self.assertTrue(response.json()['is_verified'])
        self.bank.user.refresh_from_db()
        self.assertTrue(self.bank.user.is_verified)
        self.assertFalse(self.admin.post(f'/api/bloodbanks/{self.bank.id}/unverify/').json()['is_verified'])

    def test_only_admin_can_verify(self):
        url = f'/api/bloodbanks/{self.bank.id}/verify/'
        self.assertEqual(APIClient().post(url).status_code, 401)
        self.assertEqual(client_for(self.bank.user).post(url).status_code, 403)
        self.assertEqual(client_for(make_user(Role.HOSPITAL)).post(url).status_code, 403)

    def test_admin_list_filter_and_others_forbidden(self):
        verified = make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True))
        pending = self.admin.get('/api/bloodbanks/?verified=false').json()['results']
        self.assertEqual([b['id'] for b in pending], [self.bank.id])
        self.assertEqual(self.admin.get('/api/bloodbanks/').json()['count'], 2)
        self.assertEqual(client_for(verified.user).get('/api/bloodbanks/').status_code, 403)
