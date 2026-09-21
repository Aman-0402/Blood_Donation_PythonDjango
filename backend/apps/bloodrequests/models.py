from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Role

MAX_UNITS_PER_REQUEST = 100


class BloodRequest(models.Model):
    class Urgency(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        URGENT = 'urgent', 'Urgent'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        MATCHED = 'matched', 'Matched'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'

    requester = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT, related_name='blood_requests'
    )
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='blood_requests',
    )
    patient_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    blood_group = models.ForeignKey(
        'accounts.BloodGroup', on_delete=models.PROTECT, related_name='blood_requests'
    )
    units_required = models.PositiveIntegerField()
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.NORMAL)
    location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    fulfilled_by_bloodbank = models.ForeignKey(
        'bloodbanks.BloodBank',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='fulfilled_requests',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def clean(self):
        errors = {}
        if self.units_required is not None and not 1 <= self.units_required <= MAX_UNITS_PER_REQUEST:
            errors['units_required'] = f'Units required must be between 1 and {MAX_UNITS_PER_REQUEST}.'
        if self.requester_id:
            role = self.requester.role
            if role not in (Role.SEEKER, Role.HOSPITAL):
                errors['requester'] = 'Requester must be a blood seeker or hospital.'
            elif role == Role.SEEKER and not self.patient_name:
                errors['patient_name'] = 'Patient name is required for seeker requests.'
            elif role == Role.HOSPITAL and not self.hospital_id:
                errors['hospital'] = 'Hospital is required for hospital requests.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Request #{self.pk} {self.blood_group} x{self.units_required} ({self.status})'


class RequestStatusHistory(models.Model):
    request = models.ForeignKey(
        BloodRequest, on_delete=models.CASCADE, related_name='history'
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name_plural = 'request status history'

    def __str__(self):
        return f'Request #{self.request_id}: {self.from_status or "-"} -> {self.to_status}'
