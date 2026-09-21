from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from apps.testing import blood_group, make_bloodbank, make_donor

from .models import Donation


def make_donation(donor=None, **kwargs):
    donor = donor or make_donor('O+')
    kwargs.setdefault('bloodbank', make_bloodbank())
    kwargs.setdefault('blood_group', donor.blood_group)
    kwargs.setdefault('donation_date', date.today())
    return Donation.objects.create(donor=donor, **kwargs)


class DonationTests(TestCase):
    def test_defaults_and_relationships(self):
        donation = make_donation()
        donation.full_clean()
        self.assertEqual(donation.status, Donation.Status.SCHEDULED)
        self.assertEqual(donation.donor.donations.count(), 1)

    def test_blood_group_must_match_donor(self):
        donation = make_donation(blood_group=blood_group('A+'))
        with self.assertRaises(ValidationError) as ctx:
            donation.full_clean()
        self.assertIn('blood_group', ctx.exception.message_dict)

    def test_zero_quantity_rejected(self):
        donation = make_donation(quantity=0)
        with self.assertRaises(ValidationError) as ctx:
            donation.full_clean()
        self.assertIn('quantity', ctx.exception.message_dict)

    def test_donor_protected_from_delete(self):
        donation = make_donation()
        with self.assertRaises(ProtectedError):
            donation.donor.delete()
