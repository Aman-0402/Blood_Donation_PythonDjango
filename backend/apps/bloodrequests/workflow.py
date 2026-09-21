from django.core.exceptions import ValidationError
from django.db import transaction

from .models import BloodRequest, RequestStatusHistory

Status = BloodRequest.Status

ALLOWED_TRANSITIONS = {
    Status.PENDING: {Status.APPROVED, Status.REJECTED, Status.CANCELLED},
    Status.APPROVED: {Status.MATCHED, Status.REJECTED, Status.CANCELLED},
    Status.MATCHED: {Status.PROCESSING, Status.CANCELLED},
    Status.PROCESSING: {Status.COMPLETED},
    Status.COMPLETED: set(),
    Status.CANCELLED: set(),
    Status.REJECTED: set(),
}

OWNER_CANCELLABLE = {Status.PENDING, Status.APPROVED, Status.MATCHED}


class InvalidTransition(ValidationError):
    pass


def allowed_next(status):
    return sorted(s.value for s in ALLOWED_TRANSITIONS.get(status, set()))


def record_creation(request, user):
    RequestStatusHistory.objects.create(
        request=request, from_status='', to_status=request.status, changed_by=user
    )


def change_status(request_id, new_status, user, note=''):
    """Move a request to new_status if the workflow allows it. Row-locked so concurrent changes cannot both win."""
    with transaction.atomic():
        request = BloodRequest.objects.select_for_update().get(pk=request_id)
        if new_status not in ALLOWED_TRANSITIONS.get(request.status, set()):
            raise InvalidTransition(
                f"Cannot move a {request.status} request to {new_status}. "
                f"Allowed: {', '.join(allowed_next(request.status)) or 'none'}."
            )
        previous = request.status
        request.status = new_status
        request.save(update_fields=['status', 'updated_at'])
        RequestStatusHistory.objects.create(
            request=request,
            from_status=previous,
            to_status=new_status,
            changed_by=user,
            note=note,
        )
    return request
