from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Role


class Hospital(models.Model):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='hospital_profile'
    )
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    license_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.user_id and self.user.role != Role.HOSPITAL:
            raise ValidationError({'user': 'User must have the hospital role.'})

    def __str__(self):
        return self.name
