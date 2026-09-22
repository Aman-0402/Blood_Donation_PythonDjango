from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When

from apps.accounts.compatibility import can_donate, donor_groups_for, recipient_groups_for
from apps.donors.eligibility import compute_eligibility, eligible_donors
from apps.inventory.services import search_stock
from apps.notifications.services import notify

from .models import BloodRequest, DonorResponse

Status = BloodRequest.Status
OPEN_STATUSES = (Status.APPROVED, Status.MATCHED)

BANDS = ((1, 2, '1-2'), (3, 5, '3-5'), (6, 10, '6-10'))


def band(count):
    """Coarse donor count so small numbers cannot point at one person."""
    if count <= 0:
        return '0'
    for low, high, label in BANDS:
        if low <= count <= high:
            return label
    return '10+'


def open_requests_for_donor(donor):
    """Open requests in the donor's city that the donor's blood group can safely serve."""
    groups = recipient_groups_for(donor.blood_group)
    urgency_rank = Case(
        When(urgency=BloodRequest.Urgency.CRITICAL, then=Value(0)),
        When(urgency=BloodRequest.Urgency.URGENT, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    return (
        BloodRequest.objects.filter(
            status__in=OPEN_STATUSES, blood_group__in=groups, city__iexact=donor.city
        )
        .select_related('blood_group', 'hospital')
        .annotate(urgency_rank=urgency_rank)
        .order_by('urgency_rank', '-created_at', '-id')
    )


def eligible_donors_for_request(request):
    """Eligible, available donors who can safely give to this request's blood group, in its city."""
    compatible_ids = [g.id for g in donor_groups_for(request.blood_group)]
    return eligible_donors().filter(
        blood_group_id__in=compatible_ids, city__iexact=request.city
    ).select_related('user')


def respond_to_request(donor, request_id, answer):
    if answer not in DonorResponse.Answer.values:
        raise ValidationError('Answer must be "accepted" or "declined".')
    with transaction.atomic():
        try:
            request = BloodRequest.objects.select_for_update().select_related('blood_group').get(pk=request_id)
        except BloodRequest.DoesNotExist:
            raise ValidationError('Request not found.')
        if request.status not in OPEN_STATUSES:
            raise ValidationError('This request is no longer open.')
        if (
            request.city.strip().lower() != donor.city.strip().lower()
            or not can_donate(donor.blood_group.name, request.blood_group.name)
        ):
            raise ValidationError('This request is not a match for your blood group and city.')
        if answer == DonorResponse.Answer.ACCEPTED:
            if not donor.is_available:
                raise ValidationError('Set your profile to available before accepting a request.')
            eligibility = compute_eligibility(donor)
            if not eligibility['is_eligible']:
                raise ValidationError(
                    ['You are not eligible to donate right now.', *eligibility['eligibility_reasons']]
                )
        response, _ = DonorResponse.objects.update_or_create(
            request=request, donor=donor, defaults={'answer': answer}
        )
        if answer == DonorResponse.Answer.ACCEPTED:
            donor_name = donor.user.get_full_name() or donor.user.username
            notify(
                request.requester, 'donation',
                f'{donor_name} offered to donate for your request #{request.pk}.',
                related_object_type='bloodrequest', related_object_id=request.pk,
            )
    return response


def matches_for_request(request, city=None):
    """Blood banks holding suitable stock and a banded count of donors who could help. No individuals are listed."""
    exact = request.blood_group
    compatible_ids = [g.id for g in donor_groups_for(exact)]
    city = (city or request.city or '').strip() or None
    banks = search_stock(group_ids=compatible_ids, city=city)
    for row in banks:
        row['exact'] = row['blood_group'] == exact.id
    banks.sort(key=lambda row: (not row['exact'], -row['units_available'], row['bloodbank_name']))

    donors = eligible_donors().filter(blood_group_id__in=compatible_ids)
    if city:
        donors = donors.filter(city__iexact=city)
    return {
        'city': city,
        'blood_banks': banks[:10],
        'exact_stock_units': sum(r['units_available'] for r in banks if r['exact']),
        'compatible_stock_units': sum(r['units_available'] for r in banks),
        'available_donors': band(donors.count()),
        'accepted_donors': request.donor_responses.filter(answer=DonorResponse.Answer.ACCEPTED).count(),
    }
