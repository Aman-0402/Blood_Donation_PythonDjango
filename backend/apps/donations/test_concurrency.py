import threading

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase

from apps.accounts.models import Role
from apps.inventory.models import BloodInventory
from apps.testing import make_bloodbank, make_donor, make_user, today

from . import services
from .models import Donation


class ConcurrentCompleteTests(TransactionTestCase):
    """Two staff members clicking 'complete' at once must add the blood to stock exactly once."""

    serialized_rollback = True

    def test_double_complete_adds_stock_once(self):
        bank = make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True))
        donor = make_donor('O-')
        donation = Donation.objects.create(
            donor=donor, bloodbank=bank, blood_group=donor.blood_group,
            donation_date=today(),
        )
        outcomes = []
        barrier = threading.Barrier(2)

        def worker():
            try:
                barrier.wait()
                services.complete_donation(donation.pk, bank, bank.user, quantity=2)
                outcomes.append('ok')
            except ValidationError:
                outcomes.append('rejected')
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sorted(outcomes), ['ok', 'rejected'])
        self.assertEqual(BloodInventory.objects.count(), 1)
        self.assertEqual(BloodInventory.objects.get().units, 2)
