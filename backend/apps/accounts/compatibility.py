"""ABO/Rh red-cell compatibility, derived from the group name so configured groups follow the same rules.

A donor can give to a recipient when the ABO antigens are compatible (O gives to all, AB receives from all,
otherwise the letters must match) and the Rh is compatible (Rh negative gives to all, Rh positive receives from all).
"""

from .models import BloodGroup


def _split(name):
    return name[:-1], name[-1]


def can_donate(donor_group_name, recipient_group_name):
    donor_abo, donor_rh = _split(donor_group_name)
    recipient_abo, recipient_rh = _split(recipient_group_name)
    abo_ok = donor_abo == 'O' or recipient_abo == 'AB' or donor_abo == recipient_abo
    rh_ok = donor_rh == '-' or recipient_rh == '+'
    return abo_ok and rh_ok


def donor_groups_for(recipient_group):
    """Groups that can safely give to `recipient_group` (includes the exact match)."""
    return [g for g in BloodGroup.objects.all() if can_donate(g.name, recipient_group.name)]


def recipient_groups_for(donor_group):
    """Groups that `donor_group` can safely give to (includes the exact match)."""
    return [g for g in BloodGroup.objects.all() if can_donate(donor_group.name, g.name)]
