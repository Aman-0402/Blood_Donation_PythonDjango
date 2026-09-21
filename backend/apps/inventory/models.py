from django.core.exceptions import ValidationError
from django.db import models

MAX_UNITS_PER_OPERATION = 1000


class BloodInventory(models.Model):
    """A batch of blood units at a blood bank. `units` is what is currently left in the batch."""

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        EXPIRED = 'expired', 'Expired'
        ISSUED = 'issued', 'Issued'
        DISCARDED = 'discarded', 'Discarded'

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
        ordering = ['expiry_date', 'id']

    def clean(self):
        errors = {}
        if self.units is not None:
            minimum = 1 if self.status == self.Status.AVAILABLE else 0
            if not minimum <= self.units <= MAX_UNITS_PER_OPERATION:
                errors['units'] = f'Units must be between {minimum} and {MAX_UNITS_PER_OPERATION}.'
        if self.collection_date and self.expiry_date and self.expiry_date <= self.collection_date:
            errors['expiry_date'] = 'Expiry date must be after collection date.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.bloodbank} {self.blood_group} x{self.units} ({self.status})'


class InventoryTransaction(models.Model):
    """Append-only ledger of every stock movement. `units` is signed: positive adds stock, negative removes it."""

    class Type(models.TextChoices):
        COLLECTION = 'collection', 'Collection'
        ISSUE = 'issue', 'Issue / dispatch'
        EXPIRED = 'expired', 'Expired'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    bloodbank = models.ForeignKey(
        'bloodbanks.BloodBank', on_delete=models.PROTECT, related_name='transactions'
    )
    blood_group = models.ForeignKey(
        'accounts.BloodGroup', on_delete=models.PROTECT, related_name='transactions'
    )
    batch = models.ForeignKey(
        BloodInventory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    type = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    units = models.IntegerField()
    request = models.ForeignKey(
        'bloodrequests.BloodRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions',
    )
    donation = models.ForeignKey(
        'donations.Donation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions',
    )
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.type} {self.units:+d} {self.blood_group} at {self.bloodbank}'
