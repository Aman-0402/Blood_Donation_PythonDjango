from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Role
from apps.testing import make_hospital, make_user

from .models import Hospital


class HospitalTests(TestCase):
    def test_create_and_relationship(self):
        hospital = make_hospital()
        hospital.full_clean()
        self.assertEqual(hospital.user.hospital_profile, hospital)

    def test_license_unique(self):
        make_hospital(license_number='LIC-1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Hospital.objects.create(
                user=make_user(Role.HOSPITAL), name='Dup', city='X', license_number='LIC-1'
            )

    def test_user_must_have_hospital_role(self):
        hospital = make_hospital(user=make_user(Role.DONOR))
        with self.assertRaises(ValidationError) as ctx:
            hospital.full_clean()
        self.assertIn('user', ctx.exception.message_dict)
