from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    DONOR = 'donor', 'Donor'
    SEEKER = 'seeker', 'Blood Seeker / Patient'
    HOSPITAL = 'hospital', 'Hospital'
    BLOODBANK = 'bloodbank', 'Blood Bank'


class BloodGroup(models.Model):
    name = models.CharField(max_length=3, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', Role.ADMIN)
        extra_fields.setdefault('is_verified', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SEEKER)
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.username} ({self.role})'
