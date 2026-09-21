from datetime import date, timedelta

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.bloodbanks.models import BloodBank  # noqa: F401
from apps.donations.models import Donation
from apps.notifications.models import Notification
from apps.testing import blood_group, make_bloodbank, make_donor, make_user, today

from .models import Donor


def years_ago(years):
    now = today()
    return date(now.year - years, now.month, min(now.day, 28))


def profile_payload(**overrides):
    payload = {
        'blood_group': blood_group('A+').id,
        'city': 'Pune',
        'address': '1 Main St',
        'date_of_birth': str(years_ago(30)),
    }
    payload.update(overrides)
    return payload


class DonorProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(Role.DONOR, email='private@example.com', phone='555')
        self.client.force_authenticate(self.user)

    def test_anonymous_and_wrong_roles_rejected(self):
        anon = APIClient()
        self.assertEqual(anon.post('/api/donors/', profile_payload(), format='json').status_code, 401)
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN):
            client = APIClient()
            client.force_authenticate(make_user(role))
            with self.subTest(role=role):
                self.assertEqual(client.post('/api/donors/', profile_payload(), format='json').status_code, 403)
                self.assertEqual(client.get('/api/donors/me/').status_code, 403)

    def test_create_profile(self):
        response = self.client.post('/api/donors/', profile_payload(), format='json')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['user'], self.user.id)
        self.assertEqual(body['blood_group_name'], 'A+')
        self.assertTrue(body['is_available'])
        self.assertTrue(body['is_eligible'])
        self.assertEqual(body['age'], 30)
        self.assertEqual(Donor.objects.get().user, self.user)

    def test_contact_details_not_in_profile_payload(self):
        body = self.client.post('/api/donors/', profile_payload(), format='json').json()
        self.assertNotIn('email', body)
        self.assertNotIn('phone', body)

    def test_second_profile_rejected(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        response = self.client.post('/api/donors/', profile_payload(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Donor.objects.count(), 1)

    def test_user_field_cannot_be_spoofed(self):
        other = make_user(Role.DONOR)
        response = self.client.post('/api/donors/', profile_payload(user=other.id), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Donor.objects.get().user, self.user)

    def test_validation_errors(self):
        tomorrow = str(today() + timedelta(days=1))
        cases = {
            'future dob': profile_payload(date_of_birth=tomorrow),
            'future last donation': profile_payload(last_donation_date=tomorrow),
            'unknown blood group': profile_payload(blood_group=9999),
            'missing city': {k: v for k, v in profile_payload().items() if k != 'city'},
            'donation before birth': profile_payload(
                date_of_birth='2000-01-01', last_donation_date='1999-01-01'
            ),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                self.assertEqual(self.client.post('/api/donors/', payload, format='json').status_code, 400)
        self.assertFalse(Donor.objects.exists())

    def test_me_not_found_before_profile(self):
        self.assertEqual(self.client.get('/api/donors/me/').status_code, 404)

    def test_get_and_update_me(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        self.assertEqual(self.client.get('/api/donors/me/').json()['city'], 'Pune')
        response = self.client.patch('/api/donors/me/', {'is_available': False, 'city': 'Mumbai'}, format='json')
        self.assertEqual(response.status_code, 200)
        donor = Donor.objects.get()
        self.assertFalse(donor.is_available)
        self.assertEqual(donor.city, 'Mumbai')

    def test_put_requires_full_payload(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        self.assertEqual(self.client.put('/api/donors/me/', {'city': 'X'}, format='json').status_code, 400)
        self.assertEqual(self.client.put('/api/donors/me/', profile_payload(city='Delhi'), format='json').status_code, 200)

    def test_patch_cannot_change_owner(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        other = make_user(Role.DONOR)
        self.client.patch('/api/donors/me/', {'user': other.id}, format='json')
        self.assertEqual(Donor.objects.get().user, self.user)

    def test_patch_validates_dates(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        tomorrow = str(today() + timedelta(days=1))
        response = self.client.patch('/api/donors/me/', {'last_donation_date': tomorrow}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_blood_group_locked_after_donation_recorded(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        donor = Donor.objects.get()
        Donation.objects.create(
            donor=donor, bloodbank=make_bloodbank(), blood_group=donor.blood_group,
            donation_date=today(),
        )
        response = self.client.patch('/api/donors/me/', {'blood_group': blood_group('B+').id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('blood_group', response.json())
        same = self.client.patch('/api/donors/me/', {'blood_group': blood_group('A+').id}, format='json')
        self.assertEqual(same.status_code, 200)

    def test_blood_group_changeable_without_donations(self):
        self.client.post('/api/donors/', profile_payload(), format='json')
        response = self.client.patch('/api/donors/me/', {'blood_group': blood_group('B+').id}, format='json')
        self.assertEqual(response.status_code, 200)


class DonorEligibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(Role.DONOR)
        self.client.force_authenticate(self.user)

    def eligibility(self, **profile):
        make_donor(user=self.user, **profile)
        return self.client.get('/api/donors/me/').json()

    def test_eligible_adult_with_no_donations(self):
        body = self.eligibility()
        self.assertTrue(body['is_eligible'])
        self.assertIsNone(body['next_eligible_date'])
        self.assertEqual(body['eligibility_reasons'], [])

    def test_too_young(self):
        body = self.eligibility(date_of_birth=years_ago(16))
        self.assertFalse(body['is_eligible'])
        self.assertTrue(any('at least' in r for r in body['eligibility_reasons']))

    def test_boundary_ages(self):
        self.assertTrue(self.eligibility(date_of_birth=years_ago(18))['is_eligible'])

    def test_too_old(self):
        body = self.eligibility(date_of_birth=years_ago(70))
        self.assertFalse(body['is_eligible'])
        self.assertTrue(any('at most' in r for r in body['eligibility_reasons']))

    def test_recent_self_reported_donation(self):
        last = today() - timedelta(days=10)
        body = self.eligibility(last_donation_date=last)
        self.assertFalse(body['is_eligible'])
        self.assertEqual(body['next_eligible_date'], str(last + timedelta(days=90)))

    def test_old_donation_is_fine(self):
        body = self.eligibility(last_donation_date=today() - timedelta(days=91))
        self.assertTrue(body['is_eligible'])

    def test_completed_platform_donation_counts(self):
        donor = make_donor(user=self.user)
        Donation.objects.create(
            donor=donor, bloodbank=make_bloodbank(), blood_group=donor.blood_group,
            donation_date=today() - timedelta(days=5), status=Donation.Status.COMPLETED,
        )
        self.assertFalse(self.client.get('/api/donors/me/').json()['is_eligible'])

    def test_scheduled_or_cancelled_donation_does_not_block(self):
        donor = make_donor(user=self.user)
        for status in (Donation.Status.SCHEDULED, Donation.Status.CANCELLED):
            Donation.objects.create(
                donor=donor, bloodbank=make_bloodbank(), blood_group=donor.blood_group,
                donation_date=today() - timedelta(days=5), status=status,
            )
        self.assertTrue(self.client.get('/api/donors/me/').json()['is_eligible'])

    @override_settings(DONATION_INTERVAL_DAYS=7)
    def test_interval_is_configurable(self):
        body = self.eligibility(last_donation_date=today() - timedelta(days=10))
        self.assertTrue(body['is_eligible'])


class DonorHistoryAndDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(Role.DONOR)
        self.donor = make_donor(user=self.user)
        self.bank = make_bloodbank(name='City Bank')
        self.client.force_authenticate(self.user)

    def donate(self, donor=None, days_ago=0, status=Donation.Status.COMPLETED):
        donor = donor or self.donor
        return Donation.objects.create(
            donor=donor, bloodbank=self.bank, blood_group=donor.blood_group,
            donation_date=today() - timedelta(days=days_ago), status=status,
        )

    def test_history_lists_only_own_donations_newest_first(self):
        old = self.donate(days_ago=200)
        new = self.donate(days_ago=100)
        self.donate(donor=make_donor(), days_ago=1)
        body = self.client.get('/api/donors/me/donations/').json()
        self.assertEqual([d['id'] for d in body['results']], [new.id, old.id])
        self.assertEqual(body['results'][0]['bloodbank_name'], 'City Bank')

    def test_history_404_without_profile(self):
        client = APIClient()
        client.force_authenticate(make_user(Role.DONOR))
        self.assertEqual(client.get('/api/donors/me/donations/').status_code, 404)

    def test_dashboard(self):
        self.donate(days_ago=200)
        self.donate(days_ago=100)
        self.donate(days_ago=1, status=Donation.Status.SCHEDULED)
        Notification.objects.create(user=self.user, type='alert', message='a')
        Notification.objects.create(user=self.user, type='alert', message='b', is_read=True)
        Notification.objects.create(user=make_user(), type='alert', message='not mine')
        body = self.client.get('/api/donors/me/dashboard/').json()
        self.assertEqual(body['total_donations'], 2)
        self.assertEqual(body['scheduled_donations'], 1)
        self.assertEqual(body['unread_notifications'], 1)
        self.assertEqual(len(body['recent_donations']), 3)
        self.assertTrue(body['is_available'])
        self.assertTrue(body['is_eligible'])
        self.assertEqual(body['profile']['id'], self.donor.id)

    def test_dashboard_reflects_availability_and_ineligibility(self):
        self.donor.is_available = False
        self.donor.save()
        self.donate(days_ago=3)
        body = self.client.get('/api/donors/me/dashboard/').json()
        self.assertFalse(body['is_available'])
        self.assertFalse(body['is_eligible'])
        self.assertIsNotNone(body['next_eligible_date'])

    def test_dashboard_requires_donor_role(self):
        client = APIClient()
        client.force_authenticate(make_user(Role.SEEKER))
        self.assertEqual(client.get('/api/donors/me/dashboard/').status_code, 403)


class DonorAdminAccessTests(TestCase):
    def setUp(self):
        self.donor = make_donor()
        self.other = make_donor()

    def test_admin_can_list_and_retrieve(self):
        client = APIClient()
        client.force_authenticate(make_user(Role.ADMIN))
        listing = client.get('/api/donors/').json()
        self.assertEqual(listing['count'], 2)
        self.assertEqual(client.get(f'/api/donors/{self.donor.id}/').status_code, 200)

    def test_donor_cannot_list_or_view_others(self):
        client = APIClient()
        client.force_authenticate(self.donor.user)
        self.assertEqual(client.get('/api/donors/').status_code, 403)
        self.assertEqual(client.get(f'/api/donors/{self.other.id}/').status_code, 403)

    def test_other_roles_cannot_browse_donors(self):
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK):
            client = APIClient()
            client.force_authenticate(make_user(role))
            with self.subTest(role=role):
                self.assertEqual(client.get('/api/donors/').status_code, 403)
