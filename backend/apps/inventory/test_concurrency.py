import threading

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase

from apps.accounts.models import BloodGroup
from apps.testing import make_bloodbank, make_inventory

from .models import BloodInventory, InventoryTransaction
from .services import issue_units


class ConcurrentIssueTests(TransactionTestCase):
    """Real threads, real MySQL row locks: stock must never go negative or be double-issued."""

    serialized_rollback = True  # restore seeded blood groups after the table flush

    def test_parallel_issues_cannot_oversell(self):
        bank = make_bloodbank()
        group = BloodGroup.objects.get(name='O+')
        make_inventory(bank, 'O+', units=6, days_to_expiry=5)
        make_inventory(bank, 'O+', units=4, days_to_expiry=15)
        outcomes = []
        barrier = threading.Barrier(4)

        def worker():
            try:
                barrier.wait()
                issue_units(bank, group, 3)
                outcomes.append('ok')
            except ValidationError:
                outcomes.append('short')
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 units, 3 per request: exactly 3 can succeed.
        self.assertEqual(sorted(outcomes), ['ok', 'ok', 'ok', 'short'])
        remaining = sum(BloodInventory.objects.values_list('units', flat=True))
        self.assertEqual(remaining, 1)
        issued = -sum(InventoryTransaction.objects.filter(type='issue').values_list('units', flat=True))
        self.assertEqual(issued, 9)
        self.assertEqual(remaining + issued, 10)
