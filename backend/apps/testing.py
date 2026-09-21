import itertools
from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import BloodGroup, Role, User
from apps.bloodbanks.models import BloodBank
from apps.donors.models import Donor
from apps.hospitals.models import Hospital

_counter = itertools.count(1)


def today():
    return timezone.localdate()


def make_user(role=Role.SEEKER, **kwargs):
    n = next(_counter)
    kwargs.setdefault('username', f'user{n}')
    kwargs.setdefault('email', f'user{n}@example.com')
    return User.objects.create_user(password='pass12345!', role=role, **kwargs)


def blood_group(name='O+'):
    return BloodGroup.objects.get(name=name)


def make_donor(group='O+', **kwargs):
    kwargs.setdefault('user', make_user(Role.DONOR))
    kwargs.setdefault('city', 'Pune')
    kwargs.setdefault('date_of_birth', today() - timedelta(days=365 * 30))
    return Donor.objects.create(blood_group=blood_group(group), **kwargs)


def make_hospital(**kwargs):
    n = next(_counter)
    kwargs.setdefault('user', make_user(Role.HOSPITAL))
    kwargs.setdefault('name', f'Hospital {n}')
    kwargs.setdefault('city', 'Pune')
    kwargs.setdefault('license_number', f'H-{n}')
    return Hospital.objects.create(**kwargs)


def make_bloodbank(**kwargs):
    n = next(_counter)
    kwargs.setdefault('user', make_user(Role.BLOODBANK))
    kwargs.setdefault('name', f'Bank {n}')
    kwargs.setdefault('city', 'Pune')
    kwargs.setdefault('license_number', f'B-{n}')
    return BloodBank.objects.create(**kwargs)


def make_inventory(bloodbank=None, group='B+', units=5, days_to_expiry=35, **kwargs):
    from apps.inventory.models import BloodInventory

    bloodbank = bloodbank or make_bloodbank()
    kwargs.setdefault('collection_date', today() - timedelta(days=1))
    kwargs.setdefault('expiry_date', today() + timedelta(days=days_to_expiry))
    return BloodInventory.objects.create(
        bloodbank=bloodbank, blood_group=blood_group(group), units=units, **kwargs
    )
