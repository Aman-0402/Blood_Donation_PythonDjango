from django.core.exceptions import ValidationError
from django.db import models


class Donation(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'

    donor = models.ForeignKey(
        'donors.Donor', on_delete=models.PROTECT, related_name='donations'
    )
    bloodbank = models.ForeignKey(
        'bloodbanks.BloodBank', on_delete=models.PROTECT, related_name='donations'
    )
    blood_group = models.ForeignKey(
        'accounts.BloodGroup', on_delete=models.PROTECT, related_name='donations'
    )
    quantity = models.PositiveIntegerField(default=1, help_text='Units of blood donated')
    donation_date = models.DateField()
    collection_location = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if self.quantity is not None and self.quantity < 1:
            errors['quantity'] = 'Quantity must be at least 1.'
        if self.donor_id and self.blood_group_id and self.donor.blood_group_id != self.blood_group_id:
            errors['blood_group'] = "Blood group must match the donor's blood group."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Donation {self.donor} on {self.donation_date} ({self.status})'
