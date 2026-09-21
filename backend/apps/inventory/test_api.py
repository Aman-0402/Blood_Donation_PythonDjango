from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import blood_group, make_bloodbank, make_inventory, make_user, today

from .models import BloodInventory, InventoryTransaction

Status = BloodInventory.Status


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


class InventoryAccessTests(TestCase):
    def test_anonymous_and_wrong_roles(self):
        self.assertEqual(APIClient().get('/api/inventory/').status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL):
            client = client_for(make_user(role))
            for method, url in (('get', '/api/inventory/'), ('post', '/api/inventory/'),
                                ('post', '/api/inventory/issue/'), ('get', '/api/inventory/summary/')):
                with self.subTest(role=role, url=url):
                    self.assertEqual(getattr(client, method)(url).status_code, 403)

    def test_bank_without_profile_gets_404_and_unverified_bank_403_on_writes(self):
        self.assertEqual(client_for(make_user(Role.BLOODBANK)).get('/api/inventory/').status_code, 404)
        unverified = make_bloodbank()
        client = client_for(unverified.user)
        self.assertEqual(client.get('/api/inventory/').status_code, 200)
        body = {'blood_group': blood_group('A+').id, 'units': 1}
        for url in ('/api/inventory/', '/api/inventory/issue/'):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, body, format='json').status_code, 403)
        self.assertEqual(client.post('/api/inventory/expire/').status_code, 403)

    def test_admin_is_read_only(self):
        admin = client_for(make_user(Role.ADMIN))
        self.assertEqual(admin.get('/api/inventory/').status_code, 200)
        self.assertEqual(admin.get('/api/inventory/summary/').status_code, 200)
        self.assertEqual(admin.get('/api/inventory/transactions/').status_code, 200)
        self.assertEqual(admin.post('/api/inventory/', {}, format='json').status_code, 403)
        self.assertEqual(admin.post('/api/inventory/issue/', {}, format='json').status_code, 403)


class CollectionTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.a_plus = blood_group('A+').id

    def add(self, **overrides):
        data = {'blood_group': self.a_plus, 'units': 4}
        data.update(overrides)
        return self.client.post('/api/inventory/', data, format='json')

    def test_add_units_defaults_and_ledger(self):
        response = self.add()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual((body['units'], body['status'], body['bloodbank']), (4, 'available', self.bank.id))
        self.assertEqual(body['collection_date'], str(today()))
        self.assertEqual(body['expiry_date'], str(today() + timedelta(days=35)))
        entry = InventoryTransaction.objects.get()
        self.assertEqual((entry.type, entry.units, entry.created_by), ('collection', 4, self.bank.user))

    def test_explicit_dates(self):
        response = self.add(collection_date=str(today() - timedelta(days=2)), expiry_date=str(today() + timedelta(days=10)))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['expiry_date'], str(today() + timedelta(days=10)))

    def test_validation(self):
        cases = {
            'zero units': self.add(units=0),
            'negative units': self.add(units=-3),
            'too many units': self.add(units=1001),
            'unknown group': self.add(blood_group=9999),
            'future collection': self.add(collection_date=str(today() + timedelta(days=1))),
            'expiry before collection': self.add(collection_date=str(today()), expiry_date=str(today() - timedelta(days=1))),
            'already expired': self.add(collection_date=str(today() - timedelta(days=50)), expiry_date=str(today() - timedelta(days=5))),
        }
        for name, response in cases.items():
            with self.subTest(name):
                self.assertEqual(response.status_code, 400)
        self.assertFalse(BloodInventory.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_bank_only_sees_own_batches(self):
        make_inventory(verified_bank())
        mine = make_inventory(self.bank)
        listing = self.client.get('/api/inventory/').json()['results']
        self.assertEqual([b['id'] for b in listing], [mine.id])
        other = make_inventory(verified_bank())
        self.assertEqual(self.client.get(f'/api/inventory/{other.id}/').status_code, 404)

    def test_filters_and_expiry_ordering(self):
        late = make_inventory(self.bank, 'A+', days_to_expiry=30)
        soon = make_inventory(self.bank, 'A+', days_to_expiry=5)
        make_inventory(self.bank, 'O-', days_to_expiry=10)
        rows = self.client.get(f'/api/inventory/?blood_group={self.a_plus}').json()['results']
        self.assertEqual([r['id'] for r in rows], [soon.id, late.id])
        make_inventory(self.bank, 'B+', status=Status.DISCARDED)
        self.assertEqual(self.client.get('/api/inventory/?status=discarded').json()['count'], 1)


class IssueTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.group = blood_group('O-')

    def issue(self, units, **extra):
        return self.client.post('/api/inventory/issue/', {'blood_group': self.group.id, 'units': units, **extra}, format='json')

    def test_issues_oldest_expiry_first_across_batches(self):
        soon = make_inventory(self.bank, 'O-', units=3, days_to_expiry=3)
        later = make_inventory(self.bank, 'O-', units=5, days_to_expiry=20)
        response = self.issue(4, note='walk-in')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['issued'], 4)
        soon.refresh_from_db()
        later.refresh_from_db()
        self.assertEqual((soon.units, soon.status), (0, Status.ISSUED))
        self.assertEqual((later.units, later.status), (4, Status.AVAILABLE))
        ledger = list(InventoryTransaction.objects.filter(type='issue').order_by('id').values_list('batch_id', 'units', 'note'))
        self.assertEqual(ledger, [(soon.id, -3, 'walk-in'), (later.id, -1, 'walk-in')])

    def test_insufficient_stock_changes_nothing(self):
        batch = make_inventory(self.bank, 'O-', units=3)
        response = self.issue(4)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient stock', str(response.json()))
        batch.refresh_from_db()
        self.assertEqual(batch.units, 3)
        self.assertFalse(InventoryTransaction.objects.filter(type='issue').exists())

    def test_expired_and_other_status_stock_is_not_issuable(self):
        make_inventory(self.bank, 'O-', units=9, days_to_expiry=0, collection_date=today() - timedelta(days=40))
        make_inventory(self.bank, 'O-', units=9, status=Status.RESERVED)
        make_inventory(self.bank, 'O-', units=9, status=Status.DISCARDED)
        self.assertEqual(self.issue(1).status_code, 400)

    def test_other_banks_stock_is_untouched(self):
        other = make_inventory(verified_bank(), 'O-', units=10)
        self.assertEqual(self.issue(1).status_code, 400)
        other.refresh_from_db()
        self.assertEqual(other.units, 10)

    def test_validation(self):
        make_inventory(self.bank, 'O-', units=5)
        for units in (0, -1, 1001):
            with self.subTest(units=units):
                self.assertEqual(self.issue(units).status_code, 400)
        self.assertEqual(self.client.post('/api/inventory/issue/', {'units': 1}, format='json').status_code, 400)


class ExpiryTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)

    def test_expire_marks_only_this_banks_lapsed_available_batches(self):
        old = make_inventory(self.bank, 'A+', units=6, days_to_expiry=0, collection_date=today() - timedelta(days=40))
        fresh = make_inventory(self.bank, 'A+', units=2, days_to_expiry=5)
        other_old = make_inventory(verified_bank(), 'A+', units=9, days_to_expiry=-3, collection_date=today() - timedelta(days=40))
        reserved_old = make_inventory(self.bank, 'A+', units=1, days_to_expiry=-2, collection_date=today() - timedelta(days=40), status=Status.RESERVED)
        response = self.client.post('/api/inventory/expire/')
        self.assertEqual(response.json(), {'expired_units': 6})
        for batch, expected in ((old, Status.EXPIRED), (fresh, Status.AVAILABLE), (other_old, Status.AVAILABLE), (reserved_old, Status.RESERVED)):
            batch.refresh_from_db()
            self.assertEqual(batch.status, expected)
        entry = InventoryTransaction.objects.get(type='expired')
        self.assertEqual((entry.batch_id, entry.units), (old.id, -6))

    def test_expire_is_idempotent(self):
        make_inventory(self.bank, 'A+', units=6, days_to_expiry=-1, collection_date=today() - timedelta(days=40))
        self.client.post('/api/inventory/expire/')
        self.assertEqual(self.client.post('/api/inventory/expire/').json(), {'expired_units': 0})
        self.assertEqual(InventoryTransaction.objects.filter(type='expired').count(), 1)


class AdjustmentTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.batch = make_inventory(self.bank, 'B+', units=10)

    def adjust(self, delta, reason='recount', batch=None):
        return self.client.post(f'/api/inventory/{(batch or self.batch).id}/adjust/', {'delta': delta, 'reason': reason}, format='json')

    def test_positive_and_negative_adjustments_are_logged(self):
        self.assertEqual(self.adjust(-3, 'damaged').json()['units'], 7)
        self.assertEqual(self.adjust(2, 'found extra').json()['units'], 9)
        rows = list(InventoryTransaction.objects.filter(type='adjustment').order_by('id').values_list('units', 'note'))
        self.assertEqual(rows, [(-3, 'damaged'), (2, 'found extra')])

    def test_reducing_to_zero_discards_batch(self):
        response = self.adjust(-10, 'contaminated')
        self.assertEqual((response.json()['units'], response.json()['status']), (0, 'discarded'))

    def test_invalid_adjustments(self):
        for name, response in {
            'zero delta': self.adjust(0), 'below zero': self.adjust(-11),
            'no reason': self.adjust(1, reason=''), 'too large': self.adjust(2000),
        }.items():
            with self.subTest(name):
                self.assertEqual(response.status_code, 400)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.units, 10)
        self.assertFalse(InventoryTransaction.objects.filter(type='adjustment').exists())

    def test_only_available_batches_and_only_own(self):
        expired = make_inventory(self.bank, 'B+', units=4, status=Status.EXPIRED)
        self.assertEqual(self.adjust(1, batch=expired).status_code, 400)
        other = make_inventory(verified_bank(), 'B+', units=4)
        self.assertEqual(self.adjust(1, batch=other).status_code, 404)


class SummaryAndHistoryTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)

    def test_summary_lists_all_groups_with_expiring_soon(self):
        make_inventory(self.bank, 'A+', units=4, days_to_expiry=3)
        make_inventory(self.bank, 'A+', units=6, days_to_expiry=30)
        make_inventory(self.bank, 'O-', units=2, days_to_expiry=6)
        make_inventory(verified_bank(), 'A+', units=99)
        rows = {r['blood_group_name']: r for r in self.client.get('/api/inventory/summary/').json()}
        self.assertEqual(len(rows), 8)
        self.assertEqual((rows['A+']['units_available'], rows['A+']['expiring_within_7_days']), (10, 4))
        self.assertEqual((rows['O-']['units_available'], rows['O-']['expiring_within_7_days']), (2, 2))
        self.assertEqual(rows['AB+']['units_available'], 0)

    def test_history_is_scoped_filtered_and_newest_first(self):
        self.client.post('/api/inventory/', {'blood_group': blood_group('A+').id, 'units': 5}, format='json')
        self.client.post('/api/inventory/issue/', {'blood_group': blood_group('A+').id, 'units': 2}, format='json')
        other = client_for(verified_bank().user)
        other.post('/api/inventory/', {'blood_group': blood_group('A+').id, 'units': 7}, format='json')
        body = self.client.get('/api/inventory/transactions/').json()
        self.assertEqual(body['count'], 2)
        self.assertEqual([t['type'] for t in body['results']], ['issue', 'collection'])
        self.assertEqual([t['units'] for t in body['results']], [-2, 5])
        only_issues = self.client.get('/api/inventory/transactions/?type=issue').json()
        self.assertEqual(only_issues['count'], 1)

    def test_admin_sees_every_banks_history(self):
        make_inventory(self.bank)
        self.client.post('/api/inventory/', {'blood_group': blood_group('A+').id, 'units': 1}, format='json')
        client_for(verified_bank().user).post('/api/inventory/', {'blood_group': blood_group('A+').id, 'units': 1}, format='json')
        admin = client_for(make_user(Role.ADMIN))
        self.assertEqual(admin.get('/api/inventory/transactions/').json()['count'], 2)
