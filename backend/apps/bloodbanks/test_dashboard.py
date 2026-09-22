from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.donations import services as donation_services
from apps.inventory.models import BloodInventory
from apps.testing import blood_group, make_bloodbank, make_donor, make_user, today

URL = '/api/bloodbanks/me/dashboard/'


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


class BankDashboardTests(TestCase):
    def test_access(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
        self.assertEqual(client_for(make_user(Role.BLOODBANK)).get(URL).status_code, 404)
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL, Role.ADMIN):
            self.assertEqual(client_for(make_user(role)).get(URL).status_code, 403)

    def test_stock_collected_issued_expired(self):
        bank = verified_bank()
        client = client_for(bank.user)
        client.post('/api/inventory/', {'blood_group': blood_group('A+').id, 'units': 10}, format='json')
        client.post('/api/inventory/issue/', {'blood_group': blood_group('A+').id, 'units': 3}, format='json')
        # collect legitimately (expiry must be in the future), then simulate time passing so it can expire
        client.post('/api/inventory/', {
            'blood_group': blood_group('B+').id, 'units': 4, 'expiry_date': str(today() + timedelta(days=1)),
        }, format='json')
        BloodInventory.objects.filter(bloodbank=bank, blood_group=blood_group('B+')).update(
            expiry_date=today() - timedelta(days=1)
        )
        client.post('/api/inventory/expire/')

        body = client.get(URL).json()
        self.assertEqual(body['units_collected'], 14)
        self.assertEqual(body['units_issued'], 3)
        self.assertEqual(body['units_expired'], 4)
        stock = {r['blood_group_name']: r['units_available'] for r in body['stock_by_blood_group']}
        self.assertEqual(stock['A+'], 7)
        self.assertEqual(stock['B+'], 0)

    def test_donation_and_request_counts(self):
        bank = verified_bank()
        donor = make_donor('O-')
        donation = donation_services.schedule_donation(donor, bank, today())
        body = client_for(bank.user).get(URL).json()
        self.assertEqual(body['scheduled_donations'], 1)
        self.assertEqual(body['donation_counts']['scheduled'], 1)
        donation_services.complete_donation(donation.pk, bank, bank.user, quantity=1)
        body = client_for(bank.user).get(URL).json()
        self.assertEqual(body['donation_counts']['completed'], 1)
        self.assertEqual(body['scheduled_donations'], 0)

    def test_profile_included(self):
        bank = verified_bank(name='My Bank')
        body = client_for(bank.user).get(URL).json()
        self.assertEqual(body['profile']['name'], 'My Bank')
