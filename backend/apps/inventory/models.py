from django.core.exceptions import ValidationError
from django.db import models


class BloodInventory(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        EXPIRED = 'expired', 'Expired'
        ISSUED = 'issued', 'Issued'

    bloodbank = models.ForeignKey(
        'bloodbanks.BloodBank', on_delete=models.PROTECT, related_name='inventory'
    )
    blood_group = models.ForeignKey(
        'accounts.BloodGroup', on_delete=models.PROTECT, related_name='inventory'
    )
    units = models.PositiveIntegerField()
    collection_date = models.DateField()
    expiry_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'blood inventory'

    def clean(self):
        errors = {}
        if self.units is not None and self.units < 1:
            errors['units'] = 'Units must be at least 1.'
        if self.collection_date and self.expiry_date and self.expiry_date <= self.collection_date:
            errors['expiry_date'] = 'Expiry date must be after collection date.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.bloodbank} {self.blood_group} x{self.units} ({self.status})'
