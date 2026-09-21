from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory.services import issue_units, usable_units

from .models import BloodRequest
from .workflow import change_status

Status = BloodRequest.Status


def _locked(request_id):
    return BloodRequest.objects.select_for_update().select_related('blood_group').get(pk=request_id)


def _require_own(request, bank):
    if request.fulfilled_by_bloodbank_id != bank.id:
        raise ValidationError('This request is not being fulfilled by your blood bank.')


def accept_request(request_id, bank, user):
    """Claim an approved request. Only one bank can win: the row is locked and must still be unassigned."""
    with transaction.atomic():
        request = _locked(request_id)
        if request.status != Status.APPROVED or request.fulfilled_by_bloodbank_id is not None:
            raise ValidationError('This request is no longer open for fulfilment.')
        available = usable_units(bank, request.blood_group)
        if available < request.units_required:
            raise ValidationError(
                f'Insufficient stock: {available} unit(s) of {request.blood_group.name} available, '
                f'{request.units_required} needed.'
            )
        return change_status(
            request.pk, Status.MATCHED, user, note=f'Accepted by {bank.name}',
            updates={'fulfilled_by_bloodbank': bank},
        )


def release_request(request_id, bank, user):
    """Give a matched request back so another bank can take it."""
    with transaction.atomic():
        request = _locked(request_id)
        _require_own(request, bank)
        return change_status(
            request.pk, Status.APPROVED, user, note=f'Released by {bank.name}',
            updates={'fulfilled_by_bloodbank': None},
        )


def dispatch_request(request_id, bank, user):
    """Issue the stock and start processing, atomically: if stock is short nothing changes."""
    with transaction.atomic():
        request = _locked(request_id)
        _require_own(request, bank)
        if request.status != Status.MATCHED:
            raise ValidationError(f'Only matched requests can be dispatched (this one is {request.status}).')
        issue_units(
            bank, request.blood_group, request.units_required, user=user,
            request=request, note=f'Dispatched for request #{request.pk}',
        )
        return change_status(request.pk, Status.PROCESSING, user, note='Blood dispatched')


def complete_request(request_id, bank, user):
    with transaction.atomic():
        request = _locked(request_id)
        _require_own(request, bank)
        return change_status(request.pk, Status.COMPLETED, user, note='Delivered')
