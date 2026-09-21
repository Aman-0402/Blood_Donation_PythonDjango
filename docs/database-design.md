# Database Design — Blood Donation Management System

DB: MySQL (`blood_db`). ORM: Django models.

## Entities

### User (Django built-in `auth_user`, extended via `Profile` or custom fields)
- id (PK)
- username, email, password (hashed)
- role: enum [admin, donor, seeker, hospital, bloodbank]
- phone
- is_verified: bool
- created_at, updated_at

### BloodGroup
- id (PK)
- name: enum [A+, A-, B+, B-, AB+, AB-, O+, O-]
- (kept as separate table, not hardcoded choices, so future groups/config are additive)

### Donor
- id (PK)
- user_id (FK → User, 1:1)
- blood_group_id (FK → BloodGroup)
- location / address
- latitude, longitude (optional, future search)
- date_of_birth
- last_donation_date
- is_available: bool
- eligibility_notes
- created_at, updated_at

### Hospital
- id (PK)
- user_id (FK → User, 1:1)
- name
- address, location
- license_number
- is_verified: bool
- created_at, updated_at

### BloodBank
- id (PK)
- user_id (FK → User, 1:1)
- name
- address, location
- license_number
- is_verified: bool
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
- quantity (ml or units)
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

## Notes

- All FKs use `on_delete` policy decided per-model in Phase 2 (default: `PROTECT` for records with financial/audit relevance, `CASCADE` for pure profile extensions).
- Indexes planned on: `blood_group_id`, `status` columns, `expiry_date`, `user.role`.
