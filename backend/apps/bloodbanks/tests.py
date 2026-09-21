from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Role
from apps.testing import make_bloodbank, make_user

from .models import BloodBank


class BloodBankTests(TestCase):
    def test_create_and_relationship(self):
        bank = make_bloodbank()
        bank.full_clean()
        self.assertEqual(bank.user.bloodbank_profile, bank)

    def test_license_unique(self):
        make_bloodbank(license_number='LIC-1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            BloodBank.objects.create(
                user=make_user(Role.BLOODBANK), name='Dup', city='X', license_number='LIC-1'
            )

    def test_user_must_have_bloodbank_role(self):
        bank = make_bloodbank(user=make_user(Role.HOSPITAL))
        with self.assertRaises(ValidationError) as ctx:
            bank.full_clean()
        self.assertIn('user', ctx.exception.message_dict)
