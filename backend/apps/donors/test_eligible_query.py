from datetime import date, timedelta

from django.test import TestCase

from apps.accounts.models import Role
from apps.donations.models import Donation
from apps.testing import make_bloodbank, make_donor, make_user, today

from .eligibility import compute_eligibility, eligible_donors
from .models import Donor


def years_before(day, years):
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


class EligibleDonorsQueryTests(TestCase):
    """The database query used by search must agree with the per-donor Python rules."""

    def build_donors(self, now):
        bank = make_bloodbank()
        donors = []

        def add(**kwargs):
            donor = make_donor(user=make_user(Role.DONOR), **kwargs)
            donors.append(donor)
            return donor

        # age boundaries around `now`
        for offset in (-2, -1, 0, 1, 2):
            add(date_of_birth=years_before(now, 18) + timedelta(days=offset))
            add(date_of_birth=years_before(now, 66) + timedelta(days=offset))
        add(date_of_birth=years_before(now, 30))
        add(date_of_birth=date(2000, 2, 29))
        # interval boundaries on the self-reported date
        for days_ago in (89, 90, 91):
            add(last_donation_date=now - timedelta(days=days_ago))
        # completed / scheduled platform donations
        for days_ago, status in ((10, Donation.Status.COMPLETED), (95, Donation.Status.COMPLETED),
                                 (10, Donation.Status.SCHEDULED), (10, Donation.Status.CANCELLED)):
            donor = add()
            Donation.objects.create(
                donor=donor, bloodbank=bank, blood_group=donor.blood_group,
                donation_date=now - timedelta(days=days_ago), status=status,
            )
        # both sources, later one wins
        donor = add(last_donation_date=now - timedelta(days=200))
        Donation.objects.create(
            donor=donor, bloodbank=bank, blood_group=donor.blood_group,
            donation_date=now - timedelta(days=30), status=Donation.Status.COMPLETED,
        )
        add(is_available=False)
        return donors

    def assert_query_matches_python(self, now):
        donors = self.build_donors(now)
        expected = {
            d.id for d in Donor.objects.all()
            if d.is_available and compute_eligibility(d, today=now)['is_eligible']
        }
        actual = set(eligible_donors(today=now).values_list('id', flat=True))
        self.assertEqual(actual, expected)
        self.assertTrue(expected and expected != {d.id for d in donors})  # both outcomes present

    def test_matches_python_rules_today(self):
        self.assert_query_matches_python(today())

    def test_matches_python_rules_on_a_leap_day(self):
        self.assert_query_matches_python(date(2024, 2, 29))

    def test_matches_python_rules_the_day_after_a_leap_day(self):
        self.assert_query_matches_python(date(2025, 3, 1))

    def test_matches_python_rules_on_28_february(self):
        self.assert_query_matches_python(date(2026, 2, 28))
