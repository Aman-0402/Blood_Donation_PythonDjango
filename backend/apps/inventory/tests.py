from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from apps.testing import blood_group, make_bloodbank

from .models import BloodInventory


def make_unit(**kwargs):
    kwargs.setdefault('bloodbank', make_bloodbank())
    kwargs.setdefault('blood_group', blood_group('B+'))
    kwargs.setdefault('units', 5)
    kwargs.setdefault('collection_date', date.today())
    kwargs.setdefault('expiry_date', date.today() + timedelta(days=35))
    return BloodInventory.objects.create(**kwargs)


class BloodInventoryTests(TestCase):
    def test_defaults_and_relationships(self):
        unit = make_unit()
        unit.full_clean()
        self.assertEqual(unit.status, BloodInventory.Status.AVAILABLE)
        self.assertEqual(unit.bloodbank.inventory.count(), 1)

    def test_expiry_must_follow_collection(self):
        unit = make_unit(expiry_date=date.today())
        with self.assertRaises(ValidationError) as ctx:
            unit.full_clean()
        self.assertIn('expiry_date', ctx.exception.message_dict)

    def test_zero_units_rejected(self):
        unit = make_unit(units=0)
        with self.assertRaises(ValidationError) as ctx:
            unit.full_clean()
        self.assertIn('units', ctx.exception.message_dict)

    def test_bloodbank_protected_from_delete(self):
        unit = make_unit()
        with self.assertRaises(ProtectedError):
            unit.bloodbank.delete()
