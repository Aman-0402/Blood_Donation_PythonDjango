from rest_framework.permissions import BasePermission

from .models import Role


def role_permission(*roles):
    class HasRole(BasePermission):
        message = 'You do not have permission to perform this action.'

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.role in roles)

    HasRole.__name__ = 'Has' + '_'.join(r.title() for r in roles)
    return HasRole


IsAdminRole = role_permission(Role.ADMIN)
IsDonor = role_permission(Role.DONOR)
IsSeeker = role_permission(Role.SEEKER)
IsHospital = role_permission(Role.HOSPITAL)
IsBloodBank = role_permission(Role.BLOODBANK)
