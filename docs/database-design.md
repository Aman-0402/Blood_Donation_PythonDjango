# Database Design — Blood Donation Management System

DB: MySQL (`blood_db`). ORM: Django models.

> Status: implemented in Phase 2. Deviations from the original Phase 0 draft are marked **(as built)**.

## Entities

### User (`accounts.User`, custom model extending `AbstractUser`) **(as built)**
- id (PK)
- username, email (unique), password (hashed)
- role: enum [admin, donor, seeker, hospital, bloodbank] (a `Role` choices field; no separate Role table)
- phone
- is_verified: bool — single source of truth for account verification (Hospital/BloodBank do not duplicate it)
- created_at, updated_at

### BloodGroup (`accounts.BloodGroup`) **(as built)**
- id (PK)
- name: unique, e.g. A+, A-, B+, B-, AB+, AB-, O+, O-
- Separate table seeded by data migration `accounts.0002_seed_blood_groups`, so future groups are additive.

### Donor
- id (PK)
- user_id (FK → User, 1:1)
- blood_group_id (FK → BloodGroup)
- address, city (indexed; used for search in Phase 9) **(as built)**
- date_of_birth
- last_donation_date
- is_available: bool
- eligibility_notes
- created_at, updated_at

### Hospital
- id (PK)
- user_id (FK → User, 1:1)
- name
- address, city (indexed)
- license_number (unique)
- created_at, updated_at

### BloodBank
- id (PK)
- user_id (FK → User, 1:1)
- name
- address, city (indexed)
- license_number (unique)
- created_at, updated_at

### BloodInventory
- id (PK)
- bloodbank_id (FK → BloodBank)
- blood_group_id (FK → BloodGroup)
- units: int
- collection_date
- expiry_date
- status: enum [available, reserved, expired, issued]
- created_at, updated_at

### Donation
- id (PK)
- donor_id (FK → Donor)
- bloodbank_id (FK → BloodBank)
- blood_group_id (FK → BloodGroup)
- quantity: units of blood (not ml), consistent with inventory units **(as built)**
- donation_date
- collection_location
- status: enum [scheduled, completed, cancelled, rejected]
- created_at, updated_at

### BloodRequest
- id (PK)
- requester_id (FK → User; seeker or hospital)
- hospital_id (FK → Hospital, nullable)
- patient_name (nullable, for direct seeker requests)
- blood_group_id (FK → BloodGroup)
- units_required: int
- urgency: enum [normal, urgent, critical]
- location
- status: enum [pending, approved, matched, processing, completed, cancelled, rejected]
- fulfilled_by_bloodbank_id (FK → BloodBank, nullable)
- created_at, updated_at

### Notification
- id (PK)
- user_id (FK → User)
- type: enum [request, donation, status_change, verification, alert]
- message
- related_object_type, related_object_id (generic reference)
- is_read: bool
- created_at

## Relationships

- User 1:1 Donor / Hospital / BloodBank (role-specific profile extension)
- BloodGroup 1:N Donor, BloodInventory, Donation, BloodRequest
- BloodBank 1:N BloodInventory, Donation, BloodRequest (as fulfiller)
- Hospital 1:N BloodRequest
- Donor 1:N Donation
- User 1:N Notification

## Inventory Consistency Rule

```
Current Inventory (per blood group, per bank)
  = SUM(units WHERE status = 'available')
  + completed Donations not yet reconciled into inventory
  - issued Donations
  - expired units (excluded from available count once expiry_date < today)
```

Enforced via a transaction-safe service function on donation-complete / request-fulfill / expiry-sweep — not computed ad hoc per view.

## Notes **(as built)**

- `on_delete`: `CASCADE` for profile extensions (Donor/Hospital/BloodBank → User) and Notification → User; `PROTECT` for everything else (BloodGroup, donations, requests, inventory, requester), so audit history cannot be silently deleted.
- Model-level `clean()` enforces: profile owner has the matching role; donor dates not in the future; inventory expiry after collection and units >= 1; donation blood group matches donor; request requester is seeker/hospital, seekers need a patient name, hospital requests need a hospital.
- `clean()` runs on `full_clean()`/admin forms, not on bare `.save()`. API write serializers (Phase 4+) must call the same rules.
- Indexes: `status` columns, `expiry_date`, donor/hospital/bank `city`. (`user.role` index deferred until Phase 9 search proves it needed.)
- Phase 2 API endpoints are read-only and admin-only placeholders; per-role permissions arrive in Phase 3+.
- Phase 9 additions: `BloodRequest.city` (indexed; required for seeker requests, copied from the hospital profile for hospital requests) so matching can work by location. New table `DonorResponse` (`request` CASCADE, `donor` CASCADE, `answer` accepted/declined, timestamps) with a unique constraint on (`request`, `donor`). Compatibility is computed from group names, not stored.
- Phase 8 additions: `Donation.rejection_reason`, default ordering newest donation date first, quantity capped at 10 units. `InventoryTransaction.donation` (nullable, SET_NULL) links a collection entry to the donation that produced it. Setting `DONATION_MAX_ADVANCE_DAYS` (90) limits how far ahead a donation can be booked.
- Phase 7 additions: `BloodInventory.units` is the count currently left in a batch; new status `discarded`; default ordering soonest expiry first; units may be 0 for non-available batches (available batches need at least 1). New append-only ledger `InventoryTransaction` (`bloodbank`, `blood_group`, `batch` SET_NULL, `type` collection/issue/expired/adjustment, signed `units`, `request` SET_NULL, `note`, `created_by` SET_NULL, `created_at`), read-only in Django admin. `BloodRequest` workflow gained `matched -> approved` (bank release). Setting `BLOOD_SHELF_LIFE_DAYS` (35) defaults a batch's expiry date.
- Phase 5 additions: `BloodRequest.contact_phone`, `BloodRequest.notes`, `units_required` capped at 100, default ordering newest first; new table `RequestStatusHistory` (`request`, `from_status`, `to_status`, `changed_by` SET_NULL, `note`, `created_at`) written on creation and every status change.
