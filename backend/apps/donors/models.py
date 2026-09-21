from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import Role


class Donor(models.Model):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='donor_profile'
    )
    blood_group = models.ForeignKey(
        'accounts.BloodGroup', on_delete=models.PROTECT, related_name='donors'
    )
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    date_of_birth = models.DateField()
    last_donation_date = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    eligibility_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if self.user_id and self.user.role != Role.DONOR:
            errors['user'] = 'User must have the donor role.'
        today = timezone.localdate()
        if self.date_of_birth and self.date_of_birth > today:
            errors['date_of_birth'] = 'Date of birth cannot be in the future.'
        if self.last_donation_date:
            if self.last_donation_date > today:
                errors['last_donation_date'] = 'Last donation date cannot be in the future.'
            elif self.date_of_birth and self.last_donation_date < self.date_of_birth:
                errors['last_donation_date'] = 'Last donation date cannot precede date of birth.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Donor {self.user.username} ({self.blood_group})'
