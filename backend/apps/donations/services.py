from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.donors.eligibility import compute_eligibility
from apps.donors.models import Donor
from apps.inventory.services import record_collection
from apps.notifications.services import notify

from .models import MAX_DONATION_UNITS, Donation

Status = Donation.Status


def schedule_donation(donor, bloodbank, donation_date, collection_location='', user=None):
    """Book a donation. Eligibility is judged on the donation date, not on today."""
    today = timezone.localdate()
    if donation_date < today:
        raise ValidationError('Donation date cannot be in the past.')
    if donation_date > today + timedelta(days=settings.DONATION_MAX_ADVANCE_DAYS):
        raise ValidationError(
            f'Donations can be booked at most {settings.DONATION_MAX_ADVANCE_DAYS} days ahead.'
        )
    if not bloodbank.user.is_verified:
        raise ValidationError('This blood bank is not verified yet.')
    with transaction.atomic():
        donor = Donor.objects.select_for_update().select_related('user', 'blood_group').get(pk=donor.pk)
        if not donor.is_available:
            raise ValidationError('Set your profile to available before scheduling a donation.')
        if donor.donations.filter(status=Status.SCHEDULED).exists():
            raise ValidationError('You already have a scheduled donation. Cancel it before booking another.')
        eligibility = compute_eligibility(donor, today=donation_date)
        if not eligibility['is_eligible']:
            raise ValidationError(
                ['You are not eligible to donate on that date.', *eligibility['eligibility_reasons']]
            )
        donation = Donation.objects.create(
            donor=donor,
            bloodbank=bloodbank,
            blood_group=donor.blood_group,
            donation_date=donation_date,
            collection_location=collection_location or bloodbank.address or bloodbank.name,
        )
        notify(
            bloodbank.user, 'donation',
            f'{donor.user.get_full_name() or donor.user.username} scheduled a {donor.blood_group.name} donation on {donation_date}.',
            related_object_type='donation', related_object_id=donation.pk,
        )
        return donation


def _locked_scheduled(donation_id):
    donation = Donation.objects.select_for_update().select_related('donor', 'bloodbank').get(pk=donation_id)
    if donation.status != Status.SCHEDULED:
        raise ValidationError(f'Only scheduled donations can be changed (this one is {donation.status}).')
    return donation


def cancel_donation(donation_id, donor):
    with transaction.atomic():
        donation = _locked_scheduled(donation_id)
        if donation.donor_id != donor.pk:
            raise ValidationError('This is not your donation.')
        donation.status = Status.CANCELLED
        donation.save(update_fields=['status', 'updated_at'])
    return donation


def reject_donation(donation_id, bloodbank, reason):
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('A reason is required to reject a donation.')
    with transaction.atomic():
        donation = _locked_scheduled(donation_id)
        _require_own(donation, bloodbank)
        donation.status = Status.REJECTED
        donation.rejection_reason = reason[:255]
        donation.save(update_fields=['status', 'rejection_reason', 'updated_at'])
        notify(
            donation.donor.user, 'donation',
            f'Your scheduled donation on {donation.donation_date} was declined: {reason[:255]}',
            related_object_type='donation', related_object_id=donation.pk,
        )
    return donation


def complete_donation(donation_id, bloodbank, user, quantity=1):
    """Record a completed donation: status, donor history and inventory change together or not at all."""
    if not 1 <= quantity <= MAX_DONATION_UNITS:
        raise ValidationError(f'Quantity must be between 1 and {MAX_DONATION_UNITS}.')
    with transaction.atomic():
        donation = _locked_scheduled(donation_id)
        _require_own(donation, bloodbank)
        if donation.donation_date > timezone.localdate():
            raise ValidationError('A donation cannot be completed before its scheduled date.')
        donation.status = Status.COMPLETED
        donation.quantity = quantity
        donation.save(update_fields=['status', 'quantity', 'updated_at'])
        record_collection(
            bloodbank,
            donation.blood_group,
            quantity,
            collection_date=donation.donation_date,
            user=user,
            note=f'Donation #{donation.pk}',
            donation=donation,
        )
        donor = Donor.objects.select_for_update().select_related('user').get(pk=donation.donor_id)
        if donor.last_donation_date is None or donor.last_donation_date < donation.donation_date:
            donor.last_donation_date = donation.donation_date
            donor.save(update_fields=['last_donation_date', 'updated_at'])
        notify(
            donor.user, 'donation',
            f'Thank you! Your {donation.quantity} unit donation on {donation.donation_date} was recorded.',
            related_object_type='donation', related_object_id=donation.pk,
        )
    return donation


def _require_own(donation, bloodbank):
    if donation.bloodbank_id != bloodbank.pk:
        raise ValidationError('This donation is booked at a different blood bank.')
