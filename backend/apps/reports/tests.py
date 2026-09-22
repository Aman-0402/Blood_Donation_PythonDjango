from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.bloodrequests.models import BloodRequest
from apps.bloodrequests.workflow import change_status
from apps.donations.models import Donation
from apps.testing import blood_group, make_bloodbank, make_donor, make_inventory, make_user, today

URLS = ['/api/reports/donations/', '/api/reports/requests/', '/api/reports/inventory/']


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class ReportAccessTests(TestCase):
    def test_anonymous_and_non_admin_rejected(self):
        for url in URLS:
            self.assertEqual(APIClient().get(url).status_code, 401)
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK):
            client = client_for(make_user(role))
            for url in URLS:
                with self.subTest(role=role, url=url):
                    self.assertEqual(client.get(url).status_code, 403)

    def test_admin_can_read_all(self):
        client = client_for(make_user(Role.ADMIN))
        for url in URLS:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, 200)


class DonationReportTests(TestCase):
    def test_status_and_group_and_unit_totals(self):
        bank = make_bloodbank()
        d1 = make_donor('A+')
        d2 = make_donor('O-')
        Donation.objects.create(donor=d1, bloodbank=bank, blood_group=blood_group('A+'), donation_date=today(), status=Donation.Status.COMPLETED, quantity=2)
        Donation.objects.create(donor=d2, bloodbank=bank, blood_group=blood_group('O-'), donation_date=today(), status=Donation.Status.COMPLETED, quantity=3)
        Donation.objects.create(donor=d1, bloodbank=bank, blood_group=blood_group('A+'), donation_date=today(), status=Donation.Status.SCHEDULED)
        Donation.objects.create(donor=d2, bloodbank=bank, blood_group=blood_group('O-'), donation_date=today(), status=Donation.Status.CANCELLED)

        body = client_for(make_user(Role.ADMIN)).get('/api/reports/donations/').json()
        self.assertEqual(body['by_status']['completed'], 2)
        self.assertEqual(body['by_status']['scheduled'], 1)
        self.assertEqual(body['by_status']['cancelled'], 1)
        by_group = {r['blood_group_name']: r['count'] for r in body['by_blood_group']}
        self.assertEqual(by_group['A+'], 1)  # only completed counted
        self.assertEqual(by_group['O-'], 1)
        self.assertEqual(len(body['by_blood_group']), 8)
        self.assertEqual(body['total_units_collected'], 5)

    def test_monthly_series_covers_12_months_including_zeros(self):
        bank = make_bloodbank()
        donor = make_donor('B+')
        Donation.objects.create(donor=donor, bloodbank=bank, blood_group=blood_group('B+'), donation_date=today(), status=Donation.Status.COMPLETED, quantity=4)
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/donations/').json()
        self.assertEqual(len(body['monthly']), 12)
        this_month = body['monthly'][-1]
        self.assertEqual(this_month['month'], today().strftime('%Y-%m'))
        self.assertEqual((this_month['count'], this_month['units']), (1, 4))
        self.assertEqual(body['monthly'][0]['count'], 0)

    def test_old_donation_outside_window_excluded_from_monthly(self):
        bank = make_bloodbank()
        donor = make_donor('B+')
        Donation.objects.create(
            donor=donor, bloodbank=bank, blood_group=blood_group('B+'),
            donation_date=today() - timedelta(days=400), status=Donation.Status.COMPLETED, quantity=1,
        )
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/donations/').json()
        self.assertEqual(sum(m['count'] for m in body['monthly']), 0)
        self.assertEqual(body['total_units_collected'], 1)  # all-time total still includes it


class RequestReportTests(TestCase):
    def make_request(self, **kwargs):
        data = dict(
            requester=make_user(Role.SEEKER), patient_name='P', blood_group=blood_group('A+'),
            units_required=1, city='X', location='X',
        )
        data.update(kwargs)
        return BloodRequest.objects.create(**data)

    def test_counts_by_status_urgency_group(self):
        self.make_request(status=BloodRequest.Status.PENDING, urgency='urgent')
        self.make_request(status=BloodRequest.Status.COMPLETED, urgency='critical', blood_group=blood_group('O-'))
        self.make_request(status=BloodRequest.Status.CANCELLED)
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/requests/').json()
        self.assertEqual(body['total_requests'], 3)
        self.assertEqual(body['by_status']['pending'], 1)
        self.assertEqual(body['by_status']['completed'], 1)
        self.assertEqual(body['by_urgency']['urgent'], 1)
        self.assertEqual(body['by_urgency']['critical'], 1)
        by_group = {r['blood_group_name']: r['count'] for r in body['by_blood_group']}
        self.assertEqual(by_group['A+'], 2)
        self.assertEqual(by_group['O-'], 1)

    def test_completion_rate_and_closed_count(self):
        self.make_request(status=BloodRequest.Status.COMPLETED)
        self.make_request(status=BloodRequest.Status.COMPLETED)
        self.make_request(status=BloodRequest.Status.CANCELLED)
        self.make_request(status=BloodRequest.Status.REJECTED)
        self.make_request(status=BloodRequest.Status.PENDING)
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/requests/').json()
        self.assertEqual(body['completion_rate'], 40.0)  # 2/5
        self.assertEqual(body['closed_requests'], 4)

    def test_completion_rate_zero_when_no_requests(self):
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/requests/').json()
        self.assertEqual(body['completion_rate'], 0.0)
        self.assertIsNone(body['avg_fulfillment_hours'])

    def test_avg_fulfillment_hours_only_counts_completed(self):
        req = self.make_request()
        change_status(req.pk, BloodRequest.Status.APPROVED, make_user(Role.ADMIN))
        change_status(req.pk, BloodRequest.Status.MATCHED, make_user(Role.ADMIN))
        change_status(req.pk, BloodRequest.Status.PROCESSING, make_user(Role.ADMIN))
        change_status(req.pk, BloodRequest.Status.COMPLETED, make_user(Role.ADMIN))
        body = client_for(make_user(Role.ADMIN)).get('/api/reports/requests/').json()
        self.assertIsNotNone(body['avg_fulfillment_hours'])
        self.assertGreaterEqual(body['avg_fulfillment_hours'], 0)


class InventoryReportTests(TestCase):
    def test_stock_and_expiring_soon(self):
        bank = make_bloodbank()
        make_inventory(bank, 'A+', units=6)
        make_inventory(bank, 'A+', units=3, days_to_expiry=3)
        make_inventory(bank, 'O-', units=50, days_to_expiry=-1, collection_date=str(today() - timedelta(days=40)))

        body = client_for(make_user(Role.ADMIN)).get('/api/reports/inventory/').json()
        stock = {r['blood_group_name']: r['units_available'] for r in body['by_blood_group']}
        self.assertEqual(stock['A+'], 9)
        self.assertEqual(stock['O-'], 0)  # expired excluded
        self.assertEqual(len(body['by_blood_group']), 8)

        expiring = {r['blood_group_name']: r['units'] for r in body['expiring_within_7_days']}
        self.assertEqual(expiring.get('A+'), 3)
        self.assertNotIn('O-', expiring)  # already expired, not "expiring soon"
