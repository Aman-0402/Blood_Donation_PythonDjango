from rest_framework.exceptions import NotFound, PermissionDenied

from .models import BloodBank


def get_bank(user, require_verified=True):
    """The caller's blood bank profile. Unverified banks are blocked from stock and fulfilment actions."""
    try:
        bank = BloodBank.objects.select_related('user').get(user=user)
    except BloodBank.DoesNotExist:
        raise NotFound('Blood bank profile not found.')
    if require_verified and not user.is_verified:
        raise PermissionDenied(
            'Your blood bank must be verified by an administrator before using this feature.'
        )
    return bank
