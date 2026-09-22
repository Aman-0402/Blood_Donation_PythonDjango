from django.core.exceptions import ValidationError
from django.db import transaction

from apps.notifications.services import notify, notify_many

from .models import BloodRequest, RequestStatusHistory

Status = BloodRequest.Status

ALLOWED_TRANSITIONS = {
    Status.PENDING: {Status.APPROVED, Status.REJECTED, Status.CANCELLED},
    Status.APPROVED: {Status.MATCHED, Status.REJECTED, Status.CANCELLED},
    Status.MATCHED: {Status.PROCESSING, Status.APPROVED, Status.CANCELLED},
    Status.PROCESSING: {Status.COMPLETED},
    Status.COMPLETED: set(),
    Status.CANCELLED: set(),
    Status.REJECTED: set(),
}

OWNER_CANCELLABLE = {Status.PENDING, Status.APPROVED, Status.MATCHED}

STATUS_MESSAGES = {
    Status.APPROVED: 'Your blood request #{id} was approved.',
    Status.MATCHED: 'A blood bank has been matched to your request #{id}.',
    Status.PROCESSING: 'Blood for your request #{id} is being dispatched.',
    Status.COMPLETED: 'Your blood request #{id} has been fulfilled.',
    Status.CANCELLED: 'Your blood request #{id} was cancelled.',
    Status.REJECTED: 'Your blood request #{id} was rejected.',
}

DONOR_ALERT_LIMIT = 100


class InvalidTransition(ValidationError):
    pass


def allowed_next(status):
    return sorted(s.value for s in ALLOWED_TRANSITIONS.get(status, set()))


def record_creation(request, user):
    RequestStatusHistory.objects.create(
        request=request, from_status='', to_status=request.status, changed_by=user
    )


def _notify_matching_donors(request):
    from .matching import eligible_donors_for_request

    donors = eligible_donors_for_request(request)[:DONOR_ALERT_LIMIT]
    notify_many(
        [d.user for d in donors],
        'request',
        f'A nearby blood request for {request.blood_group.name} in {request.city} needs donors.',
        related_object_type='bloodrequest',
        related_object_id=request.pk,
    )


def change_status(request_id, new_status, user, note='', updates=None):
    """Move a request to new_status if the workflow allows it, optionally setting other fields in the same
    save. Row-locked so concurrent changes cannot both win."""
    updates = updates or {}
    with transaction.atomic():
        request = BloodRequest.objects.select_for_update().select_related('requester', 'blood_group').get(pk=request_id)
        if new_status not in ALLOWED_TRANSITIONS.get(request.status, set()):
            raise InvalidTransition(
                f"Cannot move a {request.status} request to {new_status}. "
                f"Allowed: {', '.join(allowed_next(request.status)) or 'none'}."
            )
        previous = request.status
        request.status = new_status
        for field, value in updates.items():
            setattr(request, field, value)
        request.save(update_fields=['status', 'updated_at', *updates])
        RequestStatusHistory.objects.create(
            request=request,
            from_status=previous,
            to_status=new_status,
            changed_by=user,
            note=note,
        )
        if user is None or user.pk != request.requester_id:
            template = STATUS_MESSAGES.get(new_status)
            if template:
                notify(
                    request.requester, 'status_change', template.format(id=request.pk),
                    related_object_type='bloodrequest', related_object_id=request.pk,
                )
        if new_status == Status.APPROVED:
            _notify_matching_donors(request)
    return request
