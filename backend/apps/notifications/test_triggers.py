from datetime import timedelta

from django.test import TestCase

from apps.accounts.models import Role
from apps.bloodrequests.matching import respond_to_request
from apps.bloodrequests.models import BloodRequest
from apps.bloodrequests.workflow import change_status
from apps.donations import services as donation_services
from apps.testing import blood_group, make_bloodbank, make_donor, make_hospital, make_inventory, make_user, today

from .models import Notification

Status = BloodRequest.Status


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


class RequestStatusNotificationTests(TestCase):
    def setUp(self):
        self.seeker = make_user(Role.SEEKER)
        self.admin = make_user(Role.ADMIN)
        self.request = BloodRequest.objects.create(
            requester=self.seeker, patient_name='P', contact_phone='1', blood_group=blood_group('A+'),
            units_required=1, city='Pune', location='X',
        )

    def notes_for(self, user):
        return list(Notification.objects.filter(user=user).values_list('message', flat=True))

    def test_status_change_notifies_requester_not_the_actor(self):
        change_status(self.request.pk, Status.APPROVED, self.admin)
        self.assertIn(f'Your blood request #{self.request.pk} was approved.', self.notes_for(self.seeker))

    def test_self_initiated_cancel_does_not_self_notify(self):
        change_status(self.request.pk, Status.CANCELLED, self.seeker)
        self.assertEqual(self.notes_for(self.seeker), [])

    def test_admin_cancel_does_notify(self):
        change_status(self.request.pk, Status.CANCELLED, self.admin)
        self.assertIn(f'Your blood request #{self.request.pk} was cancelled.', self.notes_for(self.seeker))

    def test_approval_alerts_matching_donors_only(self):
        matching = make_donor('A+', city='Pune', user=make_user(Role.DONOR))
        wrong_group = make_donor('B+', city='Pune', user=make_user(Role.DONOR))
        wrong_city = make_donor('A+', city='Mumbai', user=make_user(Role.DONOR))
        change_status(self.request.pk, Status.APPROVED, self.admin)
        self.assertTrue(Notification.objects.filter(user=matching.user, type='request').exists())
        self.assertFalse(Notification.objects.filter(user=wrong_group.user, type='request').exists())
        self.assertFalse(Notification.objects.filter(user=wrong_city.user, type='request').exists())


class DonorAcceptNotificationTests(TestCase):
    def test_accepting_notifies_the_requester(self):
        seeker = make_user(Role.SEEKER)
        request = BloodRequest.objects.create(
            requester=seeker, patient_name='P', contact_phone='1', blood_group=blood_group('O+'),
            units_required=1, city='Pune', location='X', status=Status.APPROVED,
        )
        donor = make_donor('O+', city='Pune', user=make_user(Role.DONOR, first_name='Ravi'))
        respond_to_request(donor, request.pk, 'accepted')
        messages = list(Notification.objects.filter(user=seeker).values_list('message', flat=True))
        self.assertTrue(any('Ravi' in m for m in messages))

    def test_declining_does_not_notify(self):
        seeker = make_user(Role.SEEKER)
        request = BloodRequest.objects.create(
            requester=seeker, patient_name='P', contact_phone='1', blood_group=blood_group('O+'),
            units_required=1, city='Pune', location='X', status=Status.APPROVED,
        )
        donor = make_donor('O+', city='Pune', user=make_user(Role.DONOR))
        respond_to_request(donor, request.pk, 'declined')
        self.assertFalse(Notification.objects.filter(user=seeker).exists())


class DonationNotificationTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.donor = make_donor('B+')

    def test_schedule_notifies_the_bank(self):
        donation_services.schedule_donation(self.donor, self.bank, today())
        self.assertTrue(Notification.objects.filter(user=self.bank.user, type='donation').exists())

    def test_complete_notifies_the_donor(self):
        donation = donation_services.schedule_donation(self.donor, self.bank, today())
        donation_services.complete_donation(donation.pk, self.bank, self.bank.user, quantity=1)
        self.assertTrue(Notification.objects.filter(user=self.donor.user, type='donation').exists())

    def test_reject_notifies_the_donor_with_reason(self):
        donation = donation_services.schedule_donation(self.donor, self.bank, today())
        donation_services.reject_donation(donation.pk, self.bank, 'Low iron')
        messages = list(Notification.objects.filter(user=self.donor.user).values_list('message', flat=True))
        self.assertTrue(any('Low iron' in m for m in messages))


class VerificationNotificationTests(TestCase):
    def test_hospital_verify_and_unverify_notify(self):
        from rest_framework.test import APIClient

        hospital = make_hospital()
        admin = APIClient()
        admin.force_authenticate(make_user(Role.ADMIN))
        admin.post(f'/api/hospitals/{hospital.id}/verify/')
        self.assertTrue(
            Notification.objects.filter(user=hospital.user, type='verification', message__icontains='verified').exists()
        )
        admin.post(f'/api/hospitals/{hospital.id}/unverify/')
        self.assertTrue(
            Notification.objects.filter(user=hospital.user, type='verification', message__icontains='revoked').exists()
        )

    def test_bloodbank_verify_notifies(self):
        from rest_framework.test import APIClient

        bank = make_bloodbank()
        admin = APIClient()
        admin.force_authenticate(make_user(Role.ADMIN))
        admin.post(f'/api/bloodbanks/{bank.id}/verify/')
        self.assertTrue(Notification.objects.filter(user=bank.user, type='verification').exists())
