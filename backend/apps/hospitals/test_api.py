from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.bloodrequests.models import BloodRequest
from apps.inventory.models import BloodInventory
from apps.notifications.models import Notification
from apps.testing import blood_group, make_bloodbank, make_hospital, make_inventory, make_user

from .models import Hospital


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def profile(**overrides):
    data = {'name': 'City Care', 'city': 'Pune', 'address': '5 Hospital Rd', 'license_number': 'LIC-100'}
    data.update(overrides)
    return data


def verified_hospital(**kwargs):
    return make_hospital(user=make_user(Role.HOSPITAL, is_verified=True), **kwargs)


class HospitalProfileTests(TestCase):
    def setUp(self):
        self.user = make_user(Role.HOSPITAL)
        self.client = client_for(self.user)

    def test_role_gating(self):
        self.assertEqual(APIClient().post('/api/hospitals/', profile(), format='json').status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.BLOODBANK, Role.ADMIN):
            with self.subTest(role=role):
                self.assertEqual(client_for(make_user(role)).post('/api/hospitals/', profile(), format='json').status_code, 403)
                self.assertEqual(client_for(make_user(role)).get('/api/hospitals/me/').status_code, 403)

    def test_create_profile(self):
        response = self.client.post('/api/hospitals/', profile(), format='json')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual((body['user'], body['name'], body['is_verified']), (self.user.id, 'City Care', False))
        self.assertEqual(Hospital.objects.get().user, self.user)

    def test_cannot_create_twice(self):
        self.client.post('/api/hospitals/', profile(), format='json')
        response = self.client.post('/api/hospitals/', profile(license_number='LIC-2'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hospital.objects.count(), 1)

    def test_validation(self):
        make_hospital(license_number='TAKEN')
        cases = {
            'missing name': profile(name=''),
            'missing city': profile(city=''),
            'missing license': profile(license_number=''),
            'blank license': profile(license_number='   '),
            'duplicate license': profile(license_number='TAKEN'),
        }
        for name, data in cases.items():
            with self.subTest(name):
                self.assertEqual(self.client.post('/api/hospitals/', data, format='json').status_code, 400)
        self.assertEqual(Hospital.objects.count(), 1)

    def test_owner_and_verification_cannot_be_spoofed(self):
        other = make_user(Role.HOSPITAL)
        response = self.client.post(
            '/api/hospitals/', profile(user=other.id, is_verified=True), format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Hospital.objects.get().user, self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_me_lifecycle(self):
        self.assertEqual(self.client.get('/api/hospitals/me/').status_code, 404)
        self.client.post('/api/hospitals/', profile(), format='json')
        self.assertEqual(self.client.get('/api/hospitals/me/').json()['city'], 'Pune')
        response = self.client.patch('/api/hospitals/me/', {'city': 'Mumbai', 'is_verified': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hospital.objects.get().city, 'Mumbai')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_cannot_take_another_hospitals_license_on_update(self):
        make_hospital(license_number='TAKEN')
        self.client.post('/api/hospitals/', profile(), format='json')
        response = self.client.patch('/api/hospitals/me/', {'license_number': 'TAKEN'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_keeping_own_license_on_update_is_fine(self):
        self.client.post('/api/hospitals/', profile(), format='json')
        response = self.client.put('/api/hospitals/me/', profile(name='Renamed'), format='json')
        self.assertEqual(response.status_code, 200)

    def test_patch_cannot_change_owner(self):
        self.client.post('/api/hospitals/', profile(), format='json')
        other = make_user(Role.HOSPITAL)
        self.client.patch('/api/hospitals/me/', {'user': other.id}, format='json')
        self.assertEqual(Hospital.objects.get().user, self.user)


class HospitalVerificationTests(TestCase):
    def setUp(self):
        self.hospital = make_hospital()
        self.admin = client_for(make_user(Role.ADMIN))

    def test_admin_verifies_and_unverifies(self):
        response = self.admin.post(f'/api/hospitals/{self.hospital.id}/verify/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_verified'])
        self.hospital.user.refresh_from_db()
        self.assertTrue(self.hospital.user.is_verified)
        response = self.admin.post(f'/api/hospitals/{self.hospital.id}/unverify/')
        self.assertFalse(response.json()['is_verified'])
        self.hospital.user.refresh_from_db()
        self.assertFalse(self.hospital.user.is_verified)

    def test_only_admin_can_verify(self):
        url = f'/api/hospitals/{self.hospital.id}/verify/'
        self.assertEqual(APIClient().post(url).status_code, 401)
        self.assertEqual(client_for(self.hospital.user).post(url).status_code, 403)
        for role in (Role.DONOR, Role.SEEKER, Role.BLOODBANK):
            self.assertEqual(client_for(make_user(role)).post(url).status_code, 403)
        self.hospital.user.refresh_from_db()
        self.assertFalse(self.hospital.user.is_verified)

    def test_unknown_hospital_404(self):
        self.assertEqual(self.admin.post('/api/hospitals/99999/verify/').status_code, 404)

    def test_admin_list_and_verified_filter(self):
        verified = verified_hospital()
        listing = self.admin.get('/api/hospitals/').json()
        self.assertEqual(listing['count'], 2)
        pending = self.admin.get('/api/hospitals/?verified=false').json()['results']
        self.assertEqual([h['id'] for h in pending], [self.hospital.id])
        done = self.admin.get('/api/hospitals/?verified=true').json()['results']
        self.assertEqual([h['id'] for h in done], [verified.id])

    def test_hospitals_cannot_browse_each_other(self):
        other = make_hospital()
        client = client_for(self.hospital.user)
        self.assertEqual(client.get('/api/hospitals/').status_code, 403)
        self.assertEqual(client.get(f'/api/hospitals/{other.id}/').status_code, 403)

    def test_verification_gates_request_creation_end_to_end(self):
        def hospital_client():
            # fresh user each time: a real request reloads the user from the token
            return client_for(type(self.hospital.user).objects.get(pk=self.hospital.user_id))

        body = {
            'blood_group': blood_group('A+').id, 'units_required': 1, 'location': 'X',
        }
        self.assertEqual(hospital_client().post('/api/requests/', body, format='json').status_code, 403)
        self.admin.post(f'/api/hospitals/{self.hospital.id}/verify/')
        response = hospital_client().post('/api/requests/', body, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['hospital'], self.hospital.id)
        self.admin.post(f'/api/hospitals/{self.hospital.id}/unverify/')
        self.assertEqual(hospital_client().post('/api/requests/', body, format='json').status_code, 403)


class HospitalDashboardTests(TestCase):
    def setUp(self):
        self.hospital = verified_hospital()
        self.client = client_for(self.hospital.user)

    def add_request(self, user=None, **kwargs):
        user = user or self.hospital.user
        data = dict(requester=user, hospital=self.hospital, blood_group=blood_group('A+'),
                    units_required=1, location='X')
        data.update(kwargs)
        return BloodRequest.objects.create(**data)

    def test_404_without_profile(self):
        self.assertEqual(client_for(make_user(Role.HOSPITAL)).get('/api/hospitals/me/dashboard/').status_code, 404)

    def test_other_roles_forbidden(self):
        for role in (Role.DONOR, Role.SEEKER, Role.BLOODBANK, Role.ADMIN):
            self.assertEqual(client_for(make_user(role)).get('/api/hospitals/me/dashboard/').status_code, 403)

    def test_counts_and_lists_only_own_requests(self):
        Status = BloodRequest.Status
        self.add_request()
        self.add_request(status=Status.APPROVED)
        self.add_request(status=Status.PROCESSING)
        self.add_request(status=Status.COMPLETED)
        self.add_request(status=Status.CANCELLED)
        self.add_request(user=make_user(Role.SEEKER), hospital=None, patient_name='X')
        body = self.client.get('/api/hospitals/me/dashboard/').json()
        self.assertEqual(body['request_counts']['pending'], 1)
        self.assertEqual(body['request_counts']['approved'], 1)
        self.assertEqual(body['request_counts']['completed'], 1)
        self.assertEqual(sum(body['request_counts'].values()), 5)
        self.assertEqual(body['active_requests'], 3)
        self.assertEqual(len(body['active_request_list']), 3)
        self.assertEqual(len(body['recent_requests']), 5)
        self.assertTrue(body['is_verified'])

    def test_recent_requests_capped_at_five_newest_first(self):
        made = [self.add_request() for _ in range(7)]
        body = self.client.get('/api/hospitals/me/dashboard/').json()
        self.assertEqual([r['id'] for r in body['recent_requests']], [r.id for r in reversed(made)][:5])

    def test_available_blood_excludes_expired_and_lists_all_groups(self):
        make_inventory(group='A+', units=4)
        make_inventory(group='A+', units=6)
        make_inventory(group='O-', units=50, days_to_expiry=-2, collection_date='2000-01-01')
        make_inventory(group='B+', units=9, status=BloodInventory.Status.RESERVED)
        body = self.client.get('/api/hospitals/me/dashboard/').json()
        stock = {row['blood_group_name']: row['units_available'] for row in body['available_blood']}
        self.assertEqual(len(stock), 8)
        self.assertEqual((stock['A+'], stock['O-'], stock['B+']), (10, 0, 0))

    def test_unread_notifications_only_own(self):
        Notification.objects.create(user=self.hospital.user, type='alert', message='a')
        Notification.objects.create(user=self.hospital.user, type='alert', message='b', is_read=True)
        Notification.objects.create(user=make_user(), type='alert', message='c')
        self.assertEqual(self.client.get('/api/hospitals/me/dashboard/').json()['unread_notifications'], 1)

    def test_unverified_hospital_still_sees_dashboard(self):
        unverified = make_hospital()
        body = client_for(unverified.user).get('/api/hospitals/me/dashboard/').json()
        self.assertFalse(body['is_verified'])


class BloodAvailabilityTests(TestCase):
    URL = '/api/hospitals/blood-availability/'

    def setUp(self):
        self.hospital = verified_hospital()
        self.client = client_for(self.hospital.user)
        self.pune = make_bloodbank(name='Pune Bank', city='Pune')
        self.mumbai = make_bloodbank(name='Mumbai Bank', city='Mumbai')
        make_inventory(self.pune, 'A+', units=5)
        make_inventory(self.pune, 'A+', units=2)
        make_inventory(self.mumbai, 'A+', units=8)
        make_inventory(self.mumbai, 'O-', units=3)
        make_inventory(self.pune, 'O-', units=40, days_to_expiry=-1, collection_date='2000-01-01')

    def rows(self, query=''):
        response = self.client.get(self.URL + query)
        self.assertEqual(response.status_code, 200, response.content)
        return {(r['bloodbank__name'], r['blood_group__name']): r['units_available'] for r in response.json()}

    def test_lists_usable_stock_per_bank_and_group(self):
        self.assertEqual(
            self.rows(),
            {('Pune Bank', 'A+'): 7, ('Mumbai Bank', 'A+'): 8, ('Mumbai Bank', 'O-'): 3},
        )

    def test_filter_by_blood_group_and_city(self):
        self.assertEqual(self.rows(f'?blood_group={blood_group("O-").id}'), {('Mumbai Bank', 'O-'): 3})
        self.assertEqual(self.rows('?city=PUNE'), {('Pune Bank', 'A+'): 7})
        self.assertEqual(self.rows(f'?city=pune&blood_group={blood_group("O-").id}'), {})

    def test_invalid_parameters_rejected(self):
        self.assertEqual(self.client.get(self.URL + '?blood_group=abc').status_code, 400)
        self.assertEqual(self.client.get(self.URL + '?blood_group=0').status_code, 400)

    def test_unverified_hospital_forbidden(self):
        client = client_for(make_hospital().user)
        self.assertEqual(client.get(self.URL).status_code, 403)

    def test_admin_allowed_other_roles_not(self):
        self.assertEqual(client_for(make_user(Role.ADMIN)).get(self.URL).status_code, 200)
        self.assertEqual(APIClient().get(self.URL).status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.BLOODBANK):
            self.assertEqual(client_for(make_user(role)).get(self.URL).status_code, 403)

    def test_response_exposes_no_personal_data(self):
        row = self.client.get(self.URL).json()[0]
        self.assertEqual(
            set(row),
            {'bloodbank_id', 'bloodbank__name', 'bloodbank__city', 'blood_group_id',
             'blood_group__name', 'units_available'},
        )
