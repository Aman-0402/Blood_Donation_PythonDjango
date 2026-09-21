from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.testing import make_user

from .models import BloodGroup, Role, User


class BloodGroupTests(TestCase):
    def test_all_eight_groups_seeded(self):
        names = set(BloodGroup.objects.values_list('name', flat=True))
        self.assertEqual(names, {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'})

    def test_name_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            BloodGroup.objects.create(name='A+')


class UserTests(TestCase):
    def test_defaults(self):
        user = make_user()
        self.assertEqual(user.role, Role.SEEKER)
        self.assertFalse(user.is_verified)

    def test_password_is_hashed(self):
        user = make_user()
        self.assertNotEqual(user.password, 'pass12345!')
        self.assertTrue(user.check_password('pass12345!'))

    def test_email_unique(self):
        make_user(email='dup@example.com')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_user(email='dup@example.com')

    def test_superuser_is_verified_admin(self):
        user = User.objects.create_superuser('root', 'root@example.com', 'pass12345!')
        self.assertEqual(user.role, Role.ADMIN)
        self.assertTrue(user.is_verified)
        self.assertTrue(user.is_staff)
