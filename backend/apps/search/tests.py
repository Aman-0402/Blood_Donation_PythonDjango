from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.inventory.models import BloodInventory
from apps.testing import blood_group, make_bloodbank, make_donor, make_hospital, make_inventory, make_user, today


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


def verified_hospital(**kwargs):
    return make_hospital(user=make_user(Role.HOSPITAL, is_verified=True), **kwargs)


class SearchAccessTests(TestCase):
    URLS = ('/api/search/blood/', '/api/search/donors/', '/api/search/hospitals/')

    def test_anonymous_rejected(self):
        for url in self.URLS:
            self.assertEqual(APIClient().get(url).status_code, 401)

    def test_allowed_roles(self):
        users = [make_user(Role.SEEKER), verified_hospital().user, verified_bank().user, make_user(Role.ADMIN)]
        for user in users:
            for url in self.URLS:
                with self.subTest(role=user.role, url=url):
                    self.assertEqual(client_for(user).get(url).status_code, 200)

    def test_donors_and_unverified_orgs_blocked(self):
        for user in (make_user(Role.DONOR), make_hospital().user, make_bloodbank().user):
            for url in self.URLS:
                with self.subTest(role=user.role, url=url):
                    self.assertEqual(client_for(user).get(url).status_code, 403)


class BloodSearchTests(TestCase):
    URL = '/api/search/blood/'

    def setUp(self):
        self.client = client_for(make_user(Role.SEEKER))
        self.pune = verified_bank(name='Pune Central', city='Pune', address='1 Main Rd')
        self.mumbai = verified_bank(name='Mumbai Care', city='Mumbai')
        make_inventory(self.pune, 'A+', units=3)
        make_inventory(self.pune, 'O-', units=8)
        make_inventory(self.mumbai, 'A+', units=10)
        make_inventory(self.mumbai, 'A-', units=2)
        make_inventory(self.mumbai, 'AB+', units=6)

    def search(self, query=''):
        response = self.client.get(self.URL + query)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_exact_group_only_by_default(self):
        rows = self.search(f'?blood_group={blood_group("A+").id}')
        self.assertEqual([(r['bloodbank_name'], r['units_available'], r['exact']) for r in rows],
                         [('Mumbai Care', 10, True), ('Pune Central', 3, True)])

    def test_compatible_adds_safe_groups_and_ranks_exact_first(self):
        rows = self.search(f'?blood_group={blood_group("A+").id}&compatible=true')
        got = [(r['blood_group_name'], r['bloodbank_name'], r['exact']) for r in rows]
        self.assertEqual(got, [
            ('A+', 'Mumbai Care', True), ('A+', 'Pune Central', True),
            ('O-', 'Pune Central', False), ('A-', 'Mumbai Care', False),
        ])
        self.assertNotIn('AB+', {r['blood_group_name'] for r in rows})

    def test_result_shape_has_no_personal_data(self):
        row = self.search()[0]
        self.assertEqual(set(row), {'bloodbank', 'bloodbank_name', 'city', 'address', 'blood_group',
                                     'blood_group_name', 'units_available', 'exact'})

    def test_filters(self):
        self.assertEqual({r['bloodbank_name'] for r in self.search('?city=mumbai')}, {'Mumbai Care'})
        self.assertEqual({r['bloodbank_name'] for r in self.search(f'?bank={self.pune.id}')}, {'Pune Central'})
        self.assertEqual({r['bloodbank_name'] for r in self.search('?bank_name=central')}, {'Pune Central'})
        self.assertEqual({r['units_available'] for r in self.search('?min_units=8')}, {8, 10})
        self.assertEqual(self.search(f'?blood_group={blood_group("B+").id}'), [])

    def test_min_units_applies_to_the_summed_stock(self):
        make_inventory(self.pune, 'B+', units=3)
        make_inventory(self.pune, 'B+', units=4)
        rows = self.search(f'?blood_group={blood_group("B+").id}&min_units=7')
        self.assertEqual([r['units_available'] for r in rows], [7])

    def test_unverified_banks_expired_and_non_available_stock_are_hidden(self):
        make_inventory(make_bloodbank(name='Ghost Bank'), 'B-', units=50)
        make_inventory(self.pune, 'B-', units=9, days_to_expiry=0, collection_date=today() - timedelta(days=40))
        make_inventory(self.pune, 'B-', units=9, status=BloodInventory.Status.RESERVED)
        self.assertEqual(self.search(f'?blood_group={blood_group("B-").id}'), [])
        self.assertNotIn('Ghost Bank', {r['bloodbank_name'] for r in self.search()})

    def test_bank_that_loses_verification_disappears(self):
        self.mumbai.user.is_verified = False
        self.mumbai.user.save()
        self.assertNotIn('Mumbai Care', {r['bloodbank_name'] for r in self.search()})

    def test_invalid_parameters(self):
        for query in ('?blood_group=abc', '?blood_group=9999', '?min_units=0', '?bank=x'):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(self.URL + query).status_code, 400)

    def test_compatible_without_a_group_is_harmless(self):
        self.assertEqual(len(self.search('?compatible=true')), 5)


class DonorSearchTests(TestCase):
    URL = '/api/search/donors/'

    def setUp(self):
        self.client = client_for(make_user(Role.SEEKER))

    def donors(self, group, city, count, **kwargs):
        return [make_donor(group, city=city, user=make_user(Role.DONOR), **kwargs) for _ in range(count)]

    def search(self, query=''):
        response = self.client.get(self.URL + query)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_counts_are_banded_never_exact_or_individual(self):
        self.donors('O+', 'Pune', 1)
        self.donors('A+', 'Pune', 4)
        self.donors('B+', 'Pune', 8)
        self.donors('AB+', 'Pune', 15)
        bands = {r['blood_group_name']: r['available_donors'] for r in self.search()}
        self.assertEqual(bands, {'O+': '1-2', 'A+': '3-5', 'B+': '6-10', 'AB+': '10+'})

    def test_response_has_no_personal_fields(self):
        self.donors('O+', 'Pune', 2)
        row = self.search()[0]
        self.assertEqual(set(row), {'city', 'blood_group_name', 'available_donors'})

    def test_only_eligible_available_donors_are_counted(self):
        self.donors('O+', 'Pune', 2)
        self.donors('O+', 'Pune', 3, is_available=False)
        self.donors('O+', 'Pune', 3, last_donation_date=today() - timedelta(days=5))
        self.donors('O+', 'Pune', 3, date_of_birth=today() - timedelta(days=365 * 15))
        self.assertEqual([r['available_donors'] for r in self.search()], ['1-2'])

    def test_city_is_case_insensitive_and_grouped(self):
        self.donors('O+', 'pune', 2)
        self.donors('O+', 'PUNE', 2)
        self.donors('O+', 'Mumbai', 1)
        rows = {r['city']: r['available_donors'] for r in self.search()}
        self.assertEqual(rows, {'Mumbai': '1-2', 'Pune': '3-5'})
        self.assertEqual(list({r['city'] for r in self.search('?city=PUNE')}), ['Pune'])

    def test_compatible_search_includes_universal_donors(self):
        self.donors('O-', 'Pune', 1)
        self.donors('A+', 'Pune', 1)
        self.donors('B+', 'Pune', 1)
        exact = self.search(f'?blood_group={blood_group("A+").id}')
        self.assertEqual([r['blood_group_name'] for r in exact], ['A+'])
        wider = self.search(f'?blood_group={blood_group("A+").id}&compatible=true')
        self.assertEqual({r['blood_group_name'] for r in wider}, {'A+', 'O-'})

    def test_no_donors_is_an_empty_list(self):
        self.assertEqual(self.search(), [])


class HospitalSearchTests(TestCase):
    URL = '/api/search/hospitals/'

    def test_verified_hospitals_only_with_org_details(self):
        good = verified_hospital(name='Sunrise Hospital', city='Pune', address='2 Care Rd')
        make_hospital(name='Unverified Hospital')
        verified_hospital(name='Lakeside', city='Delhi')
        client = client_for(make_user(Role.SEEKER))
        rows = client.get(self.URL).json()
        self.assertEqual([r['name'] for r in rows], ['Lakeside', 'Sunrise Hospital'])
        self.assertEqual(set(rows[0]), {'id', 'name', 'city', 'address'})
        self.assertEqual([r['id'] for r in client.get(self.URL + '?city=pune').json()], [good.id])
        self.assertEqual([r['name'] for r in client.get(self.URL + '?name=sun').json()], ['Sunrise Hospital'])
