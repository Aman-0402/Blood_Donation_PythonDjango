from datetime import timedelta

from django.conf import settings
from django.db.models import Max
from django.utils import timezone


def age_on(date_of_birth, today):
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


def last_donation_on(donor):
    from apps.donations.models import Donation

    completed = donor.donations.filter(status=Donation.Status.COMPLETED).aggregate(
        latest=Max('donation_date')
    )['latest']
    dates = [d for d in (donor.last_donation_date, completed) if d]
    return max(dates) if dates else None


def compute_eligibility(donor, today=None):
    today = today or timezone.localdate()
    age = age_on(donor.date_of_birth, today)
    reasons = []
    if age < settings.DONOR_MIN_AGE:
        reasons.append(f'Donors must be at least {settings.DONOR_MIN_AGE} years old.')
    if age > settings.DONOR_MAX_AGE:
        reasons.append(f'Donors must be at most {settings.DONOR_MAX_AGE} years old.')

    next_eligible_date = None
    last = last_donation_on(donor)
    if last:
        candidate = last + timedelta(days=settings.DONATION_INTERVAL_DAYS)
        if candidate > today:
            next_eligible_date = candidate
            reasons.append(
                f'At least {settings.DONATION_INTERVAL_DAYS} days must pass between donations.'
            )
    return {
        'age': age,
        'is_eligible': not reasons,
        'next_eligible_date': next_eligible_date,
        'eligibility_reasons': reasons,
    }


def _years_ago(day, years):
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February in a non-leap year
        return day.replace(year=day.year - years, day=28)


def eligible_donors(today=None):
    """Donors who are available and pass the age and interval rules on `today`, evaluated in the database.

    Mirrors compute_eligibility (the tests cross-check the two) so searches do not need a query per donor.
    """
    from datetime import date

    from django.db.models import DateField, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce, Greatest

    from apps.donations.models import Donation

    from .models import Donor

    today = today or timezone.localdate()
    epoch = Value(date(1900, 1, 1), output_field=DateField())
    latest_completed = (
        Donation.objects.filter(donor=OuterRef('pk'), status=Donation.Status.COMPLETED)
        .order_by('-donation_date')
        .values('donation_date')[:1]
    )
    return (
        Donor.objects.filter(
            is_available=True,
            date_of_birth__lte=_years_ago(today, settings.DONOR_MIN_AGE),
            date_of_birth__gt=_years_ago(today, settings.DONOR_MAX_AGE + 1),
        )
        .annotate(
            last_given=Greatest(
                Coalesce('last_donation_date', epoch),
                Coalesce(Subquery(latest_completed, output_field=DateField()), epoch),
            )
        )
        .filter(last_given__lte=today - timedelta(days=settings.DONATION_INTERVAL_DAYS))
    )
