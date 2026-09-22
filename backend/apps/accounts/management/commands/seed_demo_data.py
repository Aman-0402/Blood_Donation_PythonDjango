"""Seed the database with random Indian demo data for local testing/demo purposes.

Every account created here has a username starting with "demo_" so it can never be
mistaken for a real user and can be wiped in one shot with --flush. Not run
automatically anywhere (Doc.md RULE 19: mock data must never be silently connected
to production paths) — an operator runs it by hand:

    python manage.py seed_demo_data
    python manage.py seed_demo_data --flush   # delete all demo_ users first, then reseed
    python manage.py seed_demo_data --flush --no-reseed  # just delete, don't reseed
"""

import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import BloodGroup, Role, User
from apps.bloodbanks.models import BloodBank
from apps.bloodrequests.models import BloodRequest, RequestStatusHistory
from apps.donations import services as donation_services
from apps.donations.models import Donation
from apps.donors.models import Donor
from apps.hospitals.models import Hospital
from apps.inventory.models import BloodInventory, InventoryTransaction
from apps.notifications.models import Notification

DEMO_PASSWORD = 'Demo@12345'
USERNAME_PREFIX = 'demo_'

MALE_FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Krishna', 'Ishaan', 'Rohan',
    'Kabir', 'Ayaan', 'Dhruv', 'Karan', 'Aryan', 'Yash', 'Rahul', 'Amit', 'Vikram', 'Rajesh',
    'Suresh', 'Manoj', 'Anil', 'Deepak', 'Sanjay', 'Ravi', 'Ajay', 'Naveen', 'Prakash', 'Harish',
]
FEMALE_FIRST_NAMES = [
    'Saanvi', 'Ananya', 'Aadhya', 'Diya', 'Myra', 'Ira', 'Kavya', 'Anika', 'Riya', 'Isha',
    'Priya', 'Neha', 'Pooja', 'Sneha', 'Divya', 'Shreya', 'Kiran', 'Meera', 'Lakshmi', 'Sunita',
    'Anjali', 'Deepika', 'Nisha', 'Radha', 'Swati', 'Preeti', 'Rekha', 'Geeta', 'Usha', 'Manisha',
]
LAST_NAMES = [
    'Sharma', 'Verma', 'Gupta', 'Kumar', 'Singh', 'Patel', 'Shah', 'Mehta', 'Joshi', 'Rao',
    'Reddy', 'Nair', 'Iyer', 'Pillai', 'Chatterjee', 'Banerjee', 'Mukherjee', 'Das', 'Bose', 'Ghosh',
    'Yadav', 'Chauhan', 'Malhotra', 'Kapoor', 'Bhatt', 'Desai', 'Pandey', 'Mishra', 'Tiwari', 'Agarwal',
]
CITIES = [
    'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Pune', 'Jaipur',
    'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Patna',
    'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut',
]
HOSPITAL_SUFFIXES = ['General Hospital', 'City Hospital', 'Care Hospital', 'Medical Center', 'Multispecialty Hospital']
BANK_SUFFIXES = ['Red Cross Blood Bank', 'LifeLine Blood Bank', 'City Blood Bank', 'Blood Bank & Transfusion Centre']

# Rough approximation of blood-group prevalence in India — good enough for demo data, not a medical claim.
BLOOD_GROUP_WEIGHTS = {
    'O+': 30, 'B+': 30, 'A+': 20, 'AB+': 7, 'O-': 5, 'B-': 3, 'A-': 3, 'AB-': 2,
}

DONOR_COUNT = 700
SEEKER_COUNT = 150
HOSPITAL_COUNT = 75
BLOODBANK_COUNT = 75
RECENT_DONATION_ATTEMPTS = 120
HISTORICAL_DONATION_COUNT = 250
REQUEST_COUNT = 200


def indian_name():
    if random.random() < 0.5:
        first = random.choice(MALE_FIRST_NAMES)
    else:
        first = random.choice(FEMALE_FIRST_NAMES)
    return first, random.choice(LAST_NAMES)


def indian_phone():
    return f"{random.choice('6789')}{random.randint(100000000, 999999999)}"


class Command(BaseCommand):
    help = 'Seed random Indian demo data (users, profiles, donations, requests, inventory).'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing demo_ users before reseeding.')
        parser.add_argument('--no-reseed', action='store_true', help='With --flush, only delete, do not reseed.')

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()
            if options['no_reseed']:
                return

        random.seed()
        with transaction.atomic():
            groups = {g.name: g for g in BloodGroup.objects.all()}
            donors = self._seed_donors(groups)
            seekers = self._seed_seekers()
            hospitals = self._seed_hospitals()
            banks = self._seed_bloodbanks()

        # Donations and requests call the real service layer (eligibility, inventory,
        # notifications) so the resulting ledger/stock/history are internally consistent.
        # Run outside the big atomic block since each call manages its own transaction.
        donated = self._seed_donations(donors, banks)
        requested = self._seed_requests(seekers, hospitals, groups)
        self._seed_extra_inventory(banks, groups)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(donors)} donors, {len(seekers)} seekers, {len(hospitals)} hospitals, '
            f'{len(banks)} blood banks, {donated} donations, {requested} requests.'
        ))
        self.stdout.write(f'All demo accounts share the password: {DEMO_PASSWORD}')
        self.stdout.write(f'Example login: demo_donor0001 / {DEMO_PASSWORD}')

    def _flush(self):
        qs = User.objects.filter(username__startswith=USERNAME_PREFIX)
        count = qs.count()
        Notification.objects.filter(user__in=qs).delete()
        RequestStatusHistory.objects.filter(request__requester__in=qs).delete()
        BloodRequest.objects.filter(requester__in=qs).delete()
        BloodInventory.objects.filter(bloodbank__user__in=qs).delete()
        Donor.objects.filter(user__in=qs).delete()
        Hospital.objects.filter(user__in=qs).delete()
        BloodBank.objects.filter(user__in=qs).delete()
        qs.delete()
        self.stdout.write(self.style.WARNING(f'Flushed {count} demo user(s) and their data.'))

    def _make_users(self, role, count, username_stub):
        hashed = make_password(DEMO_PASSWORD)
        users = []
        for i in range(1, count + 1):
            first, last = indian_name()
            username = f'{USERNAME_PREFIX}{username_stub}{i:04d}'
            users.append(User(
                username=username,
                email=f'{username}@example.com',
                password=hashed,
                first_name=first,
                last_name=last,
                role=role,
                phone=indian_phone(),
                is_verified=random.random() < 0.7,
            ))
        return User.objects.bulk_create(users)

    def _seed_donors(self, groups):
        users = self._make_users(Role.DONOR, DONOR_COUNT, 'donor')
        today = timezone.localdate()
        profiles = []
        for user in users:
            age_days = random.randint(18 * 365, 65 * 365)
            dob = today - timedelta(days=age_days)
            last_donation = None
            if random.random() < 0.5:
                last_donation = today - timedelta(days=random.randint(10, 500))
            group_name = random.choices(list(BLOOD_GROUP_WEIGHTS), weights=list(BLOOD_GROUP_WEIGHTS.values()))[0]
            profiles.append(Donor(
                user=user,
                blood_group=groups[group_name],
                city=random.choice(CITIES),
                address=f'{random.randint(1, 200)}, {random.choice(["MG Road", "Station Road", "Park Street", "Main Bazaar", "Ring Road"])}',
                date_of_birth=dob,
                last_donation_date=last_donation,
                is_available=random.random() < 0.85,
            ))
        Donor.objects.bulk_create(profiles)
        return list(Donor.objects.filter(user__in=users).select_related('user', 'blood_group'))

    def _seed_seekers(self):
        return self._make_users(Role.SEEKER, SEEKER_COUNT, 'seeker')

    def _seed_hospitals(self):
        users = self._make_users(Role.HOSPITAL, HOSPITAL_COUNT, 'hospital')
        profiles = []
        for i, user in enumerate(users, start=1):
            city = random.choice(CITIES)
            profiles.append(Hospital(
                user=user,
                name=f'{city} {random.choice(HOSPITAL_SUFFIXES)}',
                city=city,
                address=f'{random.randint(1, 200)}, {city}',
                license_number=f'DEMO-HOSP-{i:04d}',
            ))
        Hospital.objects.bulk_create(profiles)
        return list(Hospital.objects.filter(user__in=users).select_related('user'))

    def _seed_bloodbanks(self):
        users = self._make_users(Role.BLOODBANK, BLOODBANK_COUNT, 'bank')
        profiles = []
        for i, user in enumerate(users, start=1):
            city = random.choice(CITIES)
            profiles.append(BloodBank(
                user=user,
                name=f'{city} {random.choice(BANK_SUFFIXES)}',
                city=city,
                address=f'{random.randint(1, 200)}, {city}',
                license_number=f'DEMO-BANK-{i:04d}',
            ))
        BloodBank.objects.bulk_create(profiles)
        return list(BloodBank.objects.filter(user__in=users).select_related('user'))

    def _seed_donations(self, donors, banks):
        """Two sources, for two different purposes:

        1. Recent/today bookings go through the real schedule/complete service, so
           eligibility, inventory and the transaction ledger stay fully consistent for
           current stock. `schedule_donation` only accepts today-or-future dates, so
           this alone cannot backfill history.
        2. Older months are backfilled directly as completed Donation + ledger rows
           (no live BloodInventory batch — that stock would already be past its shelf
           life by "today", which is the correct real-world state). The live API can
           never produce this on its own; a seed script legitimately can, to give the
           Phase 13 monthly report something to show.
        """
        if not banks:
            return 0
        today = timezone.localdate()
        completed = 0

        for _ in range(RECENT_DONATION_ATTEMPTS):
            donor = random.choice(donors)
            bank = random.choice(banks)
            try:
                donation = donation_services.schedule_donation(donor, bank, today)
                if random.random() < 0.8:
                    donation_services.complete_donation(
                        donation.pk, bank, bank.user, quantity=random.randint(1, 2)
                    )
                completed += 1
            except Exception:
                continue

        historical = []
        for _ in range(HISTORICAL_DONATION_COUNT):
            donor = random.choice(donors)
            bank = random.choice(banks)
            when = today - timedelta(days=random.randint(35, 365))
            historical.append(Donation(
                donor=donor, bloodbank=bank, blood_group=donor.blood_group,
                donation_date=when, quantity=random.randint(1, 2),
                collection_location=bank.address or bank.name,
                status=Donation.Status.COMPLETED,
            ))
        Donation.objects.bulk_create(historical)
        InventoryTransaction.objects.bulk_create([
            InventoryTransaction(
                bloodbank=d.bloodbank, blood_group=d.blood_group, donation=d,
                type=InventoryTransaction.Type.COLLECTION, units=d.quantity,
                note='Demo seed: historical collection', created_by=d.bloodbank.user,
            )
            for d in historical
        ])
        return completed + len(historical)

    def _seed_requests(self, seekers, hospitals, groups):
        statuses = [s.value for s in BloodRequest.Status]
        urgencies = [u.value for u in BloodRequest.Urgency]
        created = 0
        for _ in range(REQUEST_COUNT):
            use_hospital = hospitals and random.random() < 0.3
            group = groups[random.choices(list(BLOOD_GROUP_WEIGHTS), weights=list(BLOOD_GROUP_WEIGHTS.values()))[0]]
            status = random.choice(statuses)
            if use_hospital:
                hospital = random.choice(hospitals)
                request = BloodRequest.objects.create(
                    requester=hospital.user, hospital=hospital, blood_group=group,
                    units_required=random.randint(1, 6), urgency=random.choice(urgencies),
                    city=hospital.city, location=f'{hospital.name}, {hospital.city}', status=status,
                )
            else:
                seeker = random.choice(seekers)
                first, last = indian_name()
                city = random.choice(CITIES)
                request = BloodRequest.objects.create(
                    requester=seeker, patient_name=f'{first} {last}', contact_phone=indian_phone(),
                    blood_group=group, units_required=random.randint(1, 4), urgency=random.choice(urgencies),
                    city=city, location=f'Ward {random.randint(1, 20)}, {city} Hospital', status=status,
                )
            RequestStatusHistory.objects.create(request=request, from_status='', to_status='pending')
            if status != BloodRequest.Status.PENDING:
                RequestStatusHistory.objects.create(request=request, from_status='pending', to_status=status)
            created += 1
        return created

    def _seed_extra_inventory(self, banks, groups):
        """Top up stock directly (bypassing the ledger) so every bank/group has some
        visible stock even where the sampled donations above missed a combination."""
        today = timezone.localdate()
        batches = []
        for bank in banks:
            for group in groups.values():
                if random.random() < 0.6:
                    batches.append(BloodInventory(
                        bloodbank=bank, blood_group=group, units=random.randint(1, 8),
                        collection_date=today - timedelta(days=random.randint(1, 20)),
                        expiry_date=today + timedelta(days=random.randint(5, 35)),
                    ))
        BloodInventory.objects.bulk_create(batches)
