from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from apps.accounts.models import Role
from apps.testing import blood_group, make_hospital, make_user

from .models import BloodRequest


def make_request(requester=None, **kwargs):
    requester = requester or make_user(Role.SEEKER)
    kwargs.setdefault('blood_group', blood_group('AB-'))
    kwargs.setdefault('units_required', 2)
    kwargs.setdefault('location', 'Pune')
    if requester.role == Role.SEEKER:
        kwargs.setdefault('patient_name', 'Patient One')
    return BloodRequest.objects.create(requester=requester, **kwargs)


class BloodRequestTests(TestCase):
    def test_defaults(self):
        request = make_request()
        request.full_clean()
        self.assertEqual(request.status, BloodRequest.Status.PENDING)
        self.assertEqual(request.urgency, BloodRequest.Urgency.NORMAL)
        self.assertIsNone(request.fulfilled_by_bloodbank)

    def test_hospital_request_valid_with_hospital(self):
        hospital = make_hospital()
        request = make_request(hospital.user, hospital=hospital)
        request.full_clean()
        self.assertEqual(hospital.blood_requests.count(), 1)

    def test_hospital_request_requires_hospital(self):
        request = make_request(make_user(Role.HOSPITAL))
        with self.assertRaises(ValidationError) as ctx:
            request.full_clean()
        self.assertIn('hospital', ctx.exception.message_dict)

    def test_seeker_request_requires_patient_name(self):
        request = make_request(patient_name='')
        with self.assertRaises(ValidationError) as ctx:
            request.full_clean()
        self.assertIn('patient_name', ctx.exception.message_dict)

    def test_donor_cannot_request(self):
        request = make_request(make_user(Role.DONOR))
        with self.assertRaises(ValidationError) as ctx:
            request.full_clean()
        self.assertIn('requester', ctx.exception.message_dict)

    def test_zero_units_rejected(self):
        request = make_request(units_required=0)
        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_requester_protected_from_delete(self):
        request = make_request()
        with self.assertRaises(ProtectedError):
            request.requester.delete()
