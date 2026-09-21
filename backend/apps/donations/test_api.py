from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.inventory.models import BloodInventory, InventoryTransaction
from apps.testing import blood_group, make_bloodbank, make_donor, make_user, today

from .models import Donation

Status = Donation.Status


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


def days(n):
    return today() + timedelta(days=n)


def book(donor, bank, when=0, **kwargs):
    return Donation.objects.create(
        donor=donor, bloodbank=bank, blood_group=donor.blood_group, donation_date=days(when), **kwargs
    )


class ScheduleTests(TestCase):
    def setUp(self):
        self.donor = make_donor('A-', user=make_user(Role.DONOR, phone='555-0101'))
        self.bank = verified_bank(address='12 Blood St')
        self.client = client_for(self.donor.user)

    def schedule(self, **overrides):
        data = {'bloodbank': self.bank.id, 'donation_date': str(days(3))}
        data.update(overrides)
        return self.client.post('/api/donations/', data, format='json')

    def test_schedules_donation(self):
        response = self.schedule()
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual((body['status'], body['blood_group_name'], body['quantity']), ('scheduled', 'A-', 1))
        self.assertEqual(body['collection_location'], '12 Blood St')
        self.assertEqual(body['bloodbank_name'], self.bank.name)
        self.assertNotIn('donor_phone', body)
        self.assertEqual(Donation.objects.get().donor, self.donor)

    def test_custom_location_and_today_are_allowed(self):
        response = self.schedule(donation_date=str(days(0)), collection_location='Mobile camp')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['collection_location'], 'Mobile camp')

    def test_blood_group_and_status_cannot_be_spoofed(self):
        response = self.schedule(blood_group=blood_group('O+').id, status='completed', quantity=9, donor=999)
        self.assertEqual(response.status_code, 201)
        donation = Donation.objects.get()
        self.assertEqual((donation.blood_group.name, donation.status, donation.quantity), ('A-', 'scheduled', 1))
        self.assertEqual(donation.donor, self.donor)

    def test_access_control(self):
        self.assertEqual(APIClient().post('/api/donations/', {}, format='json').status_code, 401)
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN):
            with self.subTest(role=role):
                self.assertEqual(client_for(make_user(role)).post('/api/donations/', {}, format='json').status_code, 403)

    def test_needs_donor_profile(self):
        response = client_for(make_user(Role.DONOR)).post(
            '/api/donations/', {'bloodbank': self.bank.id, 'donation_date': str(days(3))}, format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_date_rules(self):
        self.assertEqual(self.schedule(donation_date=str(days(-1))).status_code, 400)
        self.assertEqual(self.schedule(donation_date=str(days(91))).status_code, 400)
        self.assertEqual(self.schedule(donation_date=str(days(90))).status_code, 201)
        self.assertEqual(self.schedule(donation_date='not-a-date').status_code, 400)

    def test_bank_rules(self):
        unverified = make_bloodbank()
        self.assertEqual(self.schedule(bloodbank=unverified.id).status_code, 400)
        self.assertEqual(self.schedule(bloodbank=99999).status_code, 400)
        self.assertEqual(self.client.post('/api/donations/', {'donation_date': str(days(3))}, format='json').status_code, 400)
        self.assertFalse(Donation.objects.exists())

    def test_unavailable_donor_blocked(self):
        self.donor.is_available = False
        self.donor.save()
        response = self.schedule()
        self.assertEqual(response.status_code, 400)
        self.assertIn('available', str(response.json()))

    def test_only_one_scheduled_donation_at_a_time(self):
        self.assertEqual(self.schedule().status_code, 201)
        self.assertEqual(self.schedule(donation_date=str(days(10))).status_code, 400)
        self.assertEqual(Donation.objects.count(), 1)

    def test_can_rebook_after_cancelling(self):
        first = self.schedule().json()['id']
        self.client.post(f'/api/donations/{first}/cancel/')
        self.assertEqual(self.schedule().status_code, 201)

    def test_ineligible_by_age(self):
        young = make_donor(user=make_user(Role.DONOR), date_of_birth=today().replace(year=today().year - 16, day=1))
        response = client_for(young.user).post(
            '/api/donations/', {'bloodbank': self.bank.id, 'donation_date': str(days(3))}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not eligible', str(response.json()))

    def test_eligibility_is_judged_on_the_donation_date(self):
        self.donor.last_donation_date = days(-80)
        self.donor.save()
        too_soon = self.schedule(donation_date=str(days(5)))
        self.assertEqual(too_soon.status_code, 400)
        self.assertIn('90 days', str(too_soon.json()))
        self.assertEqual(self.schedule(donation_date=str(days(11))).status_code, 201)

    def test_recent_completed_platform_donation_blocks_booking(self):
        book(self.donor, self.bank, when=-10, status=Status.COMPLETED)
        self.assertEqual(self.schedule().status_code, 400)


class CancelTests(TestCase):
    def setUp(self):
        self.donor = make_donor()
        self.bank = verified_bank()
        self.donation = book(self.donor, self.bank, when=3)

    def cancel(self, user=None, donation=None):
        return client_for(user or self.donor.user).post(f'/api/donations/{(donation or self.donation).id}/cancel/')

    def test_owner_cancels(self):
        response = self.cancel()
        self.assertEqual((response.status_code, response.json()['status']), (200, 'cancelled'))

    def test_others_cannot_cancel(self):
        stranger = make_donor().user
        self.assertEqual(self.cancel(stranger).status_code, 404)
        self.assertEqual(self.cancel(self.bank.user).status_code, 403)
        self.assertEqual(self.cancel(make_user(Role.ADMIN)).status_code, 403)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Status.SCHEDULED)

    def test_only_scheduled_can_be_cancelled(self):
        for status in (Status.COMPLETED, Status.CANCELLED, Status.REJECTED):
            with self.subTest(status=status):
                Donation.objects.filter(pk=self.donation.pk).update(status=status)
                self.assertEqual(self.cancel().status_code, 400)


class BankViewTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.other_bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.donor = make_donor(user=make_user(Role.DONOR, first_name='Dana', last_name='Lee', phone='555-0142'))
        self.mine = book(self.donor, self.bank, when=2)
        self.done = book(make_donor(), self.bank, when=-5, status=Status.COMPLETED)
        self.theirs = book(make_donor(), self.other_bank, when=2)

    def ids(self, query=''):
        return {d['id'] for d in self.client.get(f'/api/donations/{query}').json()['results']}

    def test_sees_only_own_banks_donations(self):
        self.assertEqual(self.ids(), {self.mine.id, self.done.id})
        self.assertEqual(self.ids('?status=scheduled'), {self.mine.id})
        self.assertEqual(self.client.get(f'/api/donations/{self.theirs.id}/').status_code, 404)

    def test_bank_sees_donor_contact_for_its_own_appointments(self):
        body = self.client.get(f'/api/donations/{self.mine.id}/').json()
        self.assertEqual((body['donor_name'], body['donor_phone']), ('Dana Lee', '555-0142'))

    def test_donor_never_sees_other_donors_or_contact_fields(self):
        client = client_for(self.donor.user)
        listing = client.get('/api/donations/').json()['results']
        self.assertEqual([d['id'] for d in listing], [self.mine.id])
        self.assertNotIn('donor_phone', listing[0])
        self.assertEqual(client.get(f'/api/donations/{self.done.id}/').status_code, 404)

    def test_unverified_bank_blocked_and_wrong_roles(self):
        self.assertEqual(client_for(make_bloodbank().user).get('/api/donations/').status_code, 403)
        self.assertEqual(client_for(make_user(Role.BLOODBANK)).get('/api/donations/').status_code, 404)
        for role in (Role.SEEKER, Role.HOSPITAL):
            self.assertEqual(client_for(make_user(role)).get('/api/donations/').status_code, 403)
        self.assertEqual(APIClient().get('/api/donations/').status_code, 401)

    def test_admin_sees_everything_read_only(self):
        admin = client_for(make_user(Role.ADMIN))
        self.assertEqual(admin.get('/api/donations/').json()['count'], 3)
        self.assertEqual(admin.get(f'/api/donations/{self.theirs.id}/').status_code, 200)
        for action in ('complete', 'reject', 'cancel'):
            self.assertEqual(admin.post(f'/api/donations/{self.mine.id}/{action}/').status_code, 403)

    def test_newest_donation_date_first(self):
        results = self.client.get('/api/donations/').json()['results']
        self.assertEqual([d['id'] for d in results], [self.mine.id, self.done.id])


class CompleteTests(TestCase):
    def setUp(self):
        self.donor = make_donor('B+')
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.donation = book(self.donor, self.bank, when=0)

    def complete(self, donation=None, client=None, **body):
        return (client or self.client).post(f'/api/donations/{(donation or self.donation).id}/complete/', body, format='json')

    def test_complete_updates_status_history_and_inventory_together(self):
        response = self.complete(quantity=2)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual((response.json()['status'], response.json()['quantity']), ('completed', 2))

        batch = BloodInventory.objects.get()
        self.assertEqual((batch.bloodbank, batch.blood_group.name, batch.units, batch.status), (self.bank, 'B+', 2, 'available'))
        self.assertEqual(batch.collection_date, today())
        self.assertEqual(batch.expiry_date, today() + timedelta(days=35))

        entry = InventoryTransaction.objects.get()
        self.assertEqual((entry.type, entry.units, entry.donation, entry.created_by), ('collection', 2, self.donation, self.bank.user))

        self.donor.refresh_from_db()
        self.assertEqual(self.donor.last_donation_date, today())

        me = client_for(self.donor.user)
        history = me.get('/api/donors/me/donations/').json()['results']
        self.assertEqual([(d['id'], d['status']) for d in history], [(self.donation.id, 'completed')])
        profile = me.get('/api/donors/me/').json()
        self.assertFalse(profile['is_eligible'])
        self.assertEqual(profile['next_eligible_date'], str(today() + timedelta(days=90)))
        dashboard = me.get('/api/donors/me/dashboard/').json()
        self.assertEqual(dashboard['total_donations'], 1)

    def test_quantity_defaults_to_one_and_is_bounded(self):
        self.assertEqual(self.complete(quantity=0).status_code, 400)
        self.assertEqual(self.complete(quantity=11).status_code, 400)
        self.assertEqual(self.complete().json()['quantity'], 1)

    def test_cannot_complete_before_the_date(self):
        future = book(make_donor(), self.bank, when=2)
        response = self.complete(future)
        self.assertEqual(response.status_code, 400)
        future.refresh_from_db()
        self.assertEqual(future.status, Status.SCHEDULED)
        self.assertFalse(BloodInventory.objects.exists())

    def test_cannot_complete_twice_or_after_other_outcomes(self):
        self.complete()
        self.assertEqual(self.complete().status_code, 400)
        self.assertEqual(BloodInventory.objects.count(), 1)
        for status in (Status.CANCELLED, Status.REJECTED):
            other = book(make_donor(), self.bank, when=0, status=status)
            self.assertEqual(self.complete(other).status_code, 400)

    def test_other_bank_cannot_complete(self):
        rival = client_for(verified_bank().user)
        self.assertEqual(self.complete(client=rival).status_code, 404)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Status.SCHEDULED)

    def test_wrong_roles_and_unverified_bank(self):
        for user in (self.donor.user, make_user(Role.SEEKER), make_user(Role.HOSPITAL)):
            self.assertEqual(self.complete(client=client_for(user)).status_code, 403)
        unverified = make_bloodbank()
        self.assertEqual(self.complete(client=client_for(unverified.user)).status_code, 403)

    def test_failure_rolls_everything_back(self):
        stale = book(make_donor(), self.bank, when=-40)  # collected 40 days ago: past the 35-day shelf life
        donor_before = stale.donor.last_donation_date
        response = self.complete(stale)
        self.assertEqual(response.status_code, 400)
        self.assertIn('expired', str(response.json()))
        stale.refresh_from_db()
        stale.donor.refresh_from_db()
        self.assertEqual(stale.status, Status.SCHEDULED)
        self.assertEqual(stale.donor.last_donation_date, donor_before)
        self.assertFalse(BloodInventory.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_last_donation_date_never_moves_backwards(self):
        donor = make_donor(last_donation_date=today())
        older = book(donor, self.bank, when=-10)
        self.assertEqual(self.complete(older).status_code, 200)
        donor.refresh_from_db()
        self.assertEqual(donor.last_donation_date, today())

    def test_completed_blood_becomes_usable_stock(self):
        self.complete(quantity=3)
        summary = {r['blood_group_name']: r['units_available'] for r in self.client.get('/api/inventory/summary/').json()}
        self.assertEqual(summary['B+'], 3)


class RejectTests(TestCase):
    def setUp(self):
        self.donor = make_donor()
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.donation = book(self.donor, self.bank, when=1)

    def reject(self, **body):
        return self.client.post(f'/api/donations/{self.donation.id}/reject/', body, format='json')

    def test_reject_records_reason_and_leaves_inventory_alone(self):
        response = self.reject(reason='Low haemoglobin')
        self.assertEqual((response.status_code, response.json()['status']), (200, 'rejected'))
        self.assertFalse(BloodInventory.objects.exists())
        seen = client_for(self.donor.user).get(f'/api/donations/{self.donation.id}/').json()
        self.assertEqual((seen['status'], seen['rejection_reason']), ('rejected', 'Low haemoglobin'))
        self.donor.refresh_from_db()
        self.assertIsNone(self.donor.last_donation_date)

    def test_reason_is_required(self):
        self.assertEqual(self.reject().status_code, 400)
        self.assertEqual(self.reject(reason='   ').status_code, 400)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Status.SCHEDULED)

    def test_only_scheduled_and_only_own_bank(self):
        self.reject(reason='x')
        self.assertEqual(self.reject(reason='again').status_code, 400)
        other = book(make_donor(), verified_bank(), when=1)
        self.assertEqual(self.client.post(f'/api/donations/{other.id}/reject/', {'reason': 'x'}, format='json').status_code, 404)

    def test_donor_can_rebook_after_rejection(self):
        self.reject(reason='Try later')
        response = client_for(self.donor.user).post(
            '/api/donations/', {'bloodbank': self.bank.id, 'donation_date': str(days(5))}, format='json'
        )
        self.assertEqual(response.status_code, 201)


class BankDirectoryTests(TestCase):
    def test_lists_verified_banks_only_with_limited_fields(self):
        good = verified_bank(name='Alpha Bank', city='Pune', address='1 A St')
        make_bloodbank(name='Hidden Bank')
        verified_bank(name='Beta Bank', city='Mumbai')
        client = client_for(make_user(Role.DONOR))
        rows = client.get('/api/bloodbanks/directory/').json()
        self.assertEqual([r['name'] for r in rows], ['Alpha Bank', 'Beta Bank'])
        self.assertEqual(set(rows[0]), {'id', 'name', 'city', 'address'})
        self.assertEqual([r['id'] for r in client.get('/api/bloodbanks/directory/?city=PUNE').json()], [good.id])

    def test_requires_login(self):
        self.assertEqual(APIClient().get('/api/bloodbanks/directory/').status_code, 401)
