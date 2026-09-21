from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.testing import blood_group, make_bloodbank, make_inventory, today

from .models import BloodInventory
from .services import stock_by_blood_group, stock_by_bloodbank, usable_stock


class UsableStockTests(TestCase):
    def test_expiry_boundary(self):
        fresh = make_inventory(days_to_expiry=1)
        make_inventory(days_to_expiry=-1, collection_date='2000-01-01')
        make_inventory(days_to_expiry=0, collection_date='2000-01-01')
        self.assertEqual(list(usable_stock()), [fresh])

    def test_only_available_status_counts(self):
        make_inventory(status=BloodInventory.Status.RESERVED)
        make_inventory(status=BloodInventory.Status.ISSUED)
        make_inventory(status=BloodInventory.Status.EXPIRED)
        available = make_inventory()
        self.assertEqual(list(usable_stock()), [available])


class StockAggregationTests(TestCase):
    def setUp(self):
        self.bank_a = make_bloodbank(name='Alpha', city='Pune')
        self.bank_b = make_bloodbank(name='Beta', city='Mumbai')
        make_inventory(self.bank_a, 'A+', units=3)
        make_inventory(self.bank_a, 'A+', units=4)
        make_inventory(self.bank_b, 'A+', units=10)
        make_inventory(self.bank_b, 'O-', units=2)
        make_inventory(self.bank_b, 'O-', units=99, days_to_expiry=-5, collection_date='2000-01-01')

    def test_by_bloodbank_sums_batches_and_ignores_expired(self):
        rows = {(r['bloodbank__name'], r['blood_group__name']): r['units_available'] for r in stock_by_bloodbank()}
        self.assertEqual(rows, {('Alpha', 'A+'): 7, ('Beta', 'A+'): 10, ('Beta', 'O-'): 2})

    def test_filters(self):
        by_group = stock_by_bloodbank(blood_group_id=blood_group('O-').id)
        self.assertEqual([r['units_available'] for r in by_group], [2])
        by_city = stock_by_bloodbank(city='pune')
        self.assertEqual([r['bloodbank__name'] for r in by_city], ['Alpha'])
        self.assertEqual(stock_by_bloodbank(blood_group_id=blood_group('AB-').id), [])

    def test_ordering_largest_first_within_group(self):
        rows = stock_by_bloodbank(blood_group_id=blood_group('A+').id)
        self.assertEqual([r['bloodbank__name'] for r in rows], ['Beta', 'Alpha'])

    def test_by_blood_group_lists_every_group_with_zeros(self):
        rows = {r['blood_group_name']: r['units_available'] for r in stock_by_blood_group()}
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows['A+'], 17)
        self.assertEqual(rows['O-'], 2)
        self.assertEqual(rows['AB+'], 0)


class ExpireCommandTests(TestCase):
    def test_command_expires_lapsed_stock_for_every_bank(self):
        lapsed_a = make_inventory(make_bloodbank(), 'A+', units=3, days_to_expiry=-1, collection_date=today() - timedelta(days=40))
        lapsed_b = make_inventory(make_bloodbank(), 'B+', units=4, days_to_expiry=0, collection_date=today() - timedelta(days=40))
        fresh = make_inventory(make_bloodbank(), 'O+', units=5)
        out = StringIO()
        call_command('expire_blood', stdout=out)
        self.assertIn('Expired 7 unit(s)', out.getvalue())
        for batch, status in ((lapsed_a, 'expired'), (lapsed_b, 'expired'), (fresh, 'available')):
            batch.refresh_from_db()
            self.assertEqual(batch.status, status)
