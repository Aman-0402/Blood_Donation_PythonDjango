from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from apps.accounts.models import Role
from apps.testing import blood_group, make_donor, make_user

from .models import Donor


class DonorTests(TestCase):
    def test_create_and_relationships(self):
        donor = make_donor('A-')
        self.assertEqual(donor.user.donor_profile, donor)
        self.assertEqual(donor.blood_group.name, 'A-')
        self.assertTrue(donor.is_available)
        donor.full_clean()

    def test_one_profile_per_user(self):
        donor = make_donor()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Donor.objects.create(
                user=donor.user, blood_group=blood_group(), city='X',
                date_of_birth=date(1990, 1, 1),
            )

    def test_user_must_have_donor_role(self):
        donor = make_donor(user=make_user(Role.SEEKER))
        with self.assertRaises(ValidationError) as ctx:
            donor.full_clean()
        self.assertIn('user', ctx.exception.message_dict)

    def test_future_dates_rejected(self):
        tomorrow = date.today() + timedelta(days=1)
        donor = make_donor(date_of_birth=tomorrow)
        with self.assertRaises(ValidationError) as ctx:
            donor.full_clean()
        self.assertIn('date_of_birth', ctx.exception.message_dict)

        donor = make_donor(last_donation_date=tomorrow)
        with self.assertRaises(ValidationError) as ctx:
            donor.full_clean()
        self.assertIn('last_donation_date', ctx.exception.message_dict)

    def test_last_donation_before_birth_rejected(self):
        donor = make_donor(date_of_birth=date(2000, 1, 1), last_donation_date=date(1999, 1, 1))
        with self.assertRaises(ValidationError):
            donor.full_clean()

    def test_blood_group_protected_from_delete(self):
        donor = make_donor()
        with self.assertRaises(ProtectedError):
            donor.blood_group.delete()

    def test_deleting_user_removes_profile(self):
        donor = make_donor()
        donor.user.delete()
        self.assertFalse(Donor.objects.exists())
