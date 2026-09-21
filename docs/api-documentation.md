# API Documentation

Base URL (dev): `http://127.0.0.1:8000/api`. All bodies are JSON. Protected endpoints need `Authorization: Bearer <access token>`.

Errors: DRF standard. `400` validation (`{"field": ["message"]}`), `401` missing/invalid/expired token, `403` authenticated but wrong role, `404` not found (also used to hide other users' records), `405` method not allowed.

## Roles

`admin`, `donor`, `seeker`, `hospital`, `bloodbank`. Enforced server-side by `apps/accounts/permissions.py` (`IsAdminRole`, `IsDonor`, `IsSeeker`, `IsHospital`, `IsBloodBank`). The Django `is_staff` flag does not grant API admin access; only `role == admin` does.

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health/` | none | `{"status": "ok"}` |

## Authentication (Phase 3)

Access token lifetime 30 min, refresh token 7 days. Refresh tokens rotate on every refresh and the old one is blacklisted. Logout blacklists the refresh token. The access token carries a `role` claim (informational; the server always re-reads the role from the database).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register/` | none | Create account. Body: `username`, `email`, `password`, `role` (`donor`/`seeker`/`hospital`/`bloodbank`), optional `first_name`, `last_name`, `phone`. Returns `{user, access, refresh}`. `admin` cannot be self-registered; `is_staff`/`is_verified` in the body are ignored. New accounts are unverified. |
| POST | `/auth/login/` | none | Body: `username`, `password`. Returns `{access, refresh, user}`. `401` on bad credentials or inactive user. |
| POST | `/auth/refresh/` | none | Body: `refresh`. Returns new `access` and rotated `refresh`. |
| POST | `/auth/logout/` | any user | Body: `refresh`. Blacklists it (`205`). Only the token owner can blacklist their own token. |
| GET | `/auth/me/` | any user | Current user. |
| PATCH | `/auth/me/` | any user | Update `first_name`, `last_name`, `phone` only. |
| POST | `/auth/change-password/` | any user | Body: `old_password`, `new_password` (Django password validators apply). |

Passwords are validated with Django's validators (min length 8, not common, not all numeric, not similar to user attributes) and stored hashed (PBKDF2).

## Pagination

List endpoints return `{count, next, previous, results}` (page size 20, `?page=N`). `/blood-groups/` is unpaginated (returns a plain array).

## Donors (Phase 4)

Donor payload fields: `id`, `user`, `username`, `blood_group` (id), `blood_group_name`, `address`, `city`, `date_of_birth`, `last_donation_date`, `is_available`, `eligibility_notes`, `created_at`, `updated_at`, plus computed `age`, `is_eligible`, `next_eligible_date`, `eligibility_reasons`. Email and phone are never included. `user` is always the caller and cannot be set or changed by the client.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/donors/` | donor | Create own profile (one per account, `400` if it exists). Required: `blood_group`, `city`, `date_of_birth`. |
| GET | `/donors/me/` | donor | Own profile. `404` if not created yet. |
| PUT / PATCH | `/donors/me/` | donor | Update own profile. Blood group cannot change once any donation is recorded. |
| GET | `/donors/me/donations/` | donor | Own donation history, newest first (paginated). |
| GET | `/donors/me/dashboard/` | donor | `profile`, `is_available`, `is_eligible`, `next_eligible_date`, `total_donations` (completed), `scheduled_donations`, `recent_donations` (5), `unread_notifications`. |
| GET | `/donors/`, `/donors/{id}/` | admin | Browse donors. Other roles get `403` (donor privacy). |

Validation (server-side): dates not in the future, last donation not before birth, blood group must exist, city required.

Eligibility rules (configurable via env, defaults in `config/settings.py`): age between `DONOR_MIN_AGE` (18) and `DONOR_MAX_AGE` (65), and at least `DONATION_INTERVAL_DAYS` (90) since the most recent of the self-reported `last_donation_date` and the latest completed donation. `is_available` is the donor's own willingness flag and is separate from eligibility.

## Blood requests (Phase 5)

Request fields: `id`, `requester`, `requester_username`, `hospital`, `hospital_name`, `patient_name`, `contact_phone`, `notes`, `blood_group`, `blood_group_name`, `units_required` (1 to 100), `urgency` (`normal`/`urgent`/`critical`), `location`, `status`, `fulfilled_by_bloodbank`, `fulfilled_by_bloodbank_name`, `created_at`, `updated_at`, plus computed `allowed_next_statuses`. `requester`, `hospital`, `status` and `fulfilled_by_bloodbank` are server-controlled and ignored if sent by the client.

Statuses and allowed transitions (enforced in `bloodrequests/workflow.py`, row-locked, every change written to the audit history):

```text
pending    -> approved | rejected | cancelled
approved   -> matched  | rejected | cancelled
matched    -> processing | cancelled
processing -> completed
completed, cancelled, rejected: final
```

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/requests/` | seeker, hospital | Create (status `pending`). Seekers must give `patient_name`. Hospitals must have a hospital profile and be verified (`403` if unverified, checked before validation; `400` if no profile); `hospital` is set from the profile. |
| GET | `/requests/` | seeker, hospital, admin | Own requests (admin: all), newest first, paginated. Filters: `?status=`, `?urgency=`, `?blood_group=<id>`. |
| GET | `/requests/{id}/` | owner, admin | Detail. Other users get `404`. |
| PATCH / PUT | `/requests/{id}/` | owner | Edit while `pending` only (`400` otherwise). Admins cannot edit. |
| POST | `/requests/{id}/cancel/` | owner, admin | Owner: from `pending`/`approved`/`matched`. Admin: any state the workflow allows. |
| POST | `/requests/{id}/status/` | admin | Body: `status`, optional `note`. `400` with the allowed list on an invalid jump. |
| GET | `/requests/{id}/history/` | owner, admin | Audit trail: `from_status`, `to_status`, `changed_by_username`, `note`, `created_at`. |

Requests cannot be deleted (audit trail). Blood banks will get their processing/complete transitions in Phase 7; notifications on status changes arrive in Phase 10.

## Reference data and admin lookups (Phase 2, permissions updated in Phase 3)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/blood-groups/` | any user | The 8 blood groups. |
| GET | `/users/` | admin | User list (no passwords). |

Read-only admin-only placeholder lists (superseded module by module in later phases): `/donations/`, `/inventory/`, `/notifications/`, `/bloodbanks/`, `/hospitals/`.
