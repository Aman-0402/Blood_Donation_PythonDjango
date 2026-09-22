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

Request fields: `id`, `requester`, `requester_username`, `hospital`, `hospital_name`, `patient_name`, `contact_phone`, `notes`, `blood_group`, `blood_group_name`, `units_required` (1 to 100), `urgency` (`normal`/`urgent`/`critical`), `city` (Phase 9), `location`, `status`, `fulfilled_by_bloodbank`, `fulfilled_by_bloodbank_name`, `created_at`, `updated_at`, plus computed `allowed_next_statuses`. `requester`, `hospital`, `status` and `fulfilled_by_bloodbank` are server-controlled and ignored if sent by the client.

Statuses and allowed transitions (enforced in `bloodrequests/workflow.py`, row-locked, every change written to the audit history):

```text
pending    -> approved | rejected | cancelled
approved   -> matched  | rejected | cancelled
matched    -> processing | approved (released by the bank) | cancelled
processing -> completed
completed, cancelled, rejected: final
```

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/requests/` | seeker, hospital | Create (status `pending`). Seekers must give `patient_name`. Hospitals must have a hospital profile and be verified (`403` if unverified, checked before validation; `400` if no profile); `hospital` is set from the profile. |
| GET | `/requests/` | seeker, hospital, admin, verified bank | Own requests (admin: all; bank: open approved plus assigned, see below), newest first, paginated. Filters: `?status=`, `?urgency=`, `?blood_group=<id>`. |
| GET | `/requests/{id}/` | owner, admin | Detail. Other users get `404`. |
| PATCH / PUT | `/requests/{id}/` | owner | Edit while `pending` only (`400` otherwise). Admins cannot edit. |
| POST | `/requests/{id}/cancel/` | owner, admin | Owner: from `pending`/`approved`/`matched`. Admin: any state the workflow allows. |
| POST | `/requests/{id}/status/` | admin | Body: `status`, optional `note`. `400` with the allowed list on an invalid jump. |
| GET | `/requests/{id}/history/` | owner, admin | Audit trail: `from_status`, `to_status`, `changed_by_username`, `note`, `created_at`. |

Requests cannot be deleted (audit trail). Notifications on status changes arrive in Phase 10.

Blood bank fulfilment (Phase 7). Verified banks see `approved` requests nobody has claimed yet, plus requests assigned to them (`404` for anything else). Until a bank owns a request, `requester`, `requester_username`, `patient_name`, `contact_phone` and `notes` are omitted from what it sees. Banks cannot use the requester/admin endpoints (`cancel`, `status`, `history`, create/edit).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/requests/{id}/accept/` | bank | `approved` and unassigned -> `matched`, assigns the bank. Needs enough usable stock of the group. The row is locked, so exactly one bank wins a race. |
| POST | `/requests/{id}/dispatch/` | assigned bank | `matched` -> `processing`. Issues the requested units from the bank's stock (oldest expiry first) in the same transaction; if stock is short nothing changes (`400`). Ledger entries link to the request. |
| POST | `/requests/{id}/complete/` | assigned bank | `processing` -> `completed`. |
| POST | `/requests/{id}/release/` | assigned bank | `matched` -> `approved`, unassigns the bank so another can take it. |

Unverified banks get `403` on all of these and on the request list.

## Blood banks (Phase 7)

Profile payload matches hospitals: `id`, `user`, `username`, `name`, `address`, `city`, `license_number` (unique), `is_verified` (read-only), timestamps.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/bloodbanks/` | bloodbank | Create own profile (one per account). |
| GET | `/bloodbanks/me/` | bloodbank | Own profile (`404` until created). |
| PUT / PATCH | `/bloodbanks/me/` | bloodbank | Update own profile. |
| GET | `/bloodbanks/`, `/bloodbanks/{id}/` | admin | Browse banks. `?verified=true` or `?verified=false`. |
| POST | `/bloodbanks/{id}/verify/`, `/unverify/` | admin | Set verification. |

## Inventory (Phase 7)

Stock lives in batches (`BloodInventory`: blood group, units left, collection date, expiry date, status `available`/`reserved`/`expired`/`issued`/`discarded`). Every movement is appended to a ledger (`InventoryTransaction`) with signed units. All stock changes run in row-locked transactions (`inventory/services.py`), so concurrent requests cannot oversell; this is covered by tests using real threads on MySQL.

Banks see only their own batches and history; admins can read everything but cannot change stock. Reads work for unverified banks; every write needs a verified bank (`403` otherwise, `404` if no profile).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/inventory/` | verified bank | Record a collection: `blood_group`, `units` (1 to 1000), optional `collection_date` (not future, default today), `expiry_date` (default collection + `BLOOD_SHELF_LIFE_DAYS`, 35; must be after collection and after today), `note`. |
| GET | `/inventory/`, `/inventory/{id}/` | bank, admin | Batches, soonest expiry first. Filters `?status=`, `?blood_group=`. |
| POST | `/inventory/issue/` | verified bank | Direct dispatch: `blood_group`, `units`, `note`. Takes from batches closest to expiry first; all-or-nothing (`400` with the available count if short). Emptied batches become `issued`. |
| POST | `/inventory/expire/` | verified bank | Marks the bank's available batches at or past expiry as `expired`; returns `{expired_units}`. Idempotent. |
| POST | `/inventory/{id}/adjust/` | verified bank | `delta` (non-zero), `reason` (required). Only `available` batches; cannot go negative; reaching zero marks the batch `discarded`. |
| GET | `/inventory/summary/` | bank, admin | Usable units per blood group (all 8 listed) with `expiring_within_7_days`. |
| GET | `/inventory/transactions/` | bank, admin | Ledger, newest first, paginated. Filters `?type=` (collection, issue, expired, adjustment), `?blood_group=`. |

Cron: `python manage.py expire_blood` expires lapsed stock for every bank; schedule it daily.

## Hospitals (Phase 6)

Hospital payload: `id`, `user`, `username`, `name`, `address`, `city`, `license_number` (unique), `is_verified` (read-only, mirrors `User.is_verified`), `created_at`, `updated_at`. `user` and `is_verified` cannot be set by the client.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/hospitals/` | hospital | Create own profile (one per account). Required: `name`, `city`, `license_number`. |
| GET | `/hospitals/me/` | hospital | Own profile (`404` until created). |
| PUT / PATCH | `/hospitals/me/` | hospital | Update own profile. |
| GET | `/hospitals/me/dashboard/` | hospital | `profile`, `is_verified`, `request_counts` (every status), `active_requests`, `active_request_list` (5), `recent_requests` (5), `available_blood` (units per blood group across all banks, expired excluded, all 8 groups listed), `unread_notifications`. Works while unverified. |
| GET | `/hospitals/blood-availability/` | verified hospital, admin | Usable stock per blood bank and blood group. Optional `?blood_group=<id>`, `?city=<name>` (case-insensitive). Unverified hospitals get `403`. Returns only bank name, city, blood group and units (no personal data). |
| GET | `/hospitals/`, `/hospitals/{id}/` | admin | Browse hospitals. `?verified=true` or `?verified=false` filters by verification. |
| POST | `/hospitals/{id}/verify/`, `/hospitals/{id}/unverify/` | admin | Set the hospital account's verification. |

Hospitals request blood through `/requests/` (Phase 5): they need a profile and a verified account. Their request list, tracking, cancel and history are the same endpoints, scoped to their own requests.

Usable stock rule (`inventory/services.py`): status `available` and `expiry_date` strictly after today (a unit expires on its expiry date), summed across batches.

## Donations (Phase 8)

Donation payload: `id`, `donor`, `bloodbank`, `bloodbank_name`, `blood_group`, `blood_group_name`, `quantity` (units, 1 to 10), `donation_date`, `collection_location`, `status` (`scheduled`, `completed`, `cancelled`, `rejected`), `rejection_reason`, timestamps. Banks and admins additionally get `donor_name` and `donor_phone` (the donor chose to book with that bank); donors never see other donors' data. Lists are newest donation date first, paginated, filter `?status=`.

Only `scheduled` donations can change state: to `completed` (bank), `rejected` (bank) or `cancelled` (donor). Every change is row-locked, so double clicks or concurrent staff cannot apply it twice.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/donations/` | donor | Schedule: `bloodbank` (verified banks only), `donation_date` (today up to `DONATION_MAX_ADVANCE_DAYS`, 90, ahead), optional `collection_location` (defaults to the bank's address). Blood group comes from the donor profile. Rules: donor profile exists (`404`), profile is available, only one scheduled donation at a time, and eligibility is evaluated on the donation date (age range and the interval since the last donation). `400` with the reasons otherwise. |
| GET | `/donations/`, `/donations/{id}/` | donor (own), verified bank (its own), admin (all) | Others get `404`. |
| POST | `/donations/{id}/cancel/` | donor (owner) | `scheduled` -> `cancelled`. |
| POST | `/donations/{id}/complete/` | verified bank (its own) | Optional `quantity` (default 1). Not allowed before the donation date. In one transaction: status -> `completed`, a new inventory batch is added with a ledger entry linked to the donation, and the donor's `last_donation_date` moves forward (never backwards). If any step fails (for example the collection date is past the shelf life) nothing changes. |
| POST | `/donations/{id}/reject/` | verified bank (its own) | Body `reason` (required). `scheduled` -> `rejected`; no stock change. The donor can book again. |
| GET | `/bloodbanks/directory/` | any signed-in user | Verified banks only: `id`, `name`, `city`, `address`. Optional `?city=`. |

Admins are read-only here (`403` on actions). Eligibility and history feed the donor endpoints from Phase 4: completed donations count toward `total_donations` and push `next_eligible_date` out by the donation interval.

## Search and matching (Phase 9)

Matching uses standard ABO/Rh red-cell compatibility (`accounts/compatibility.py`, derived from the group name): O gives to all, AB receives from all, otherwise ABO letters must match; Rh negative gives to all, Rh positive only to Rh positive. Exact matches are always ranked before compatible ones.

Search is open to signed-in seekers, hospitals, blood banks and admins. Hospitals and banks must be verified (`403` otherwise); donors get `403`. Only verified banks' usable stock is searched (available, not expired).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/search/blood/` | Stock per bank and group: `bloodbank`, `bloodbank_name`, `city`, `address`, `blood_group`, `blood_group_name`, `units_available`, `exact`. Filters: `blood_group` (id), `compatible=true` (also include groups that can safely be given), `city`, `bank` (id), `bank_name` (contains), `min_units` (applies to the summed stock). Exact first, then most units. Invalid parameters give `400`. |
| GET | `/search/donors/` | Eligible, available donors as banded counts per city and blood group: `city`, `blood_group_name`, `available_donors` (`1-2`, `3-5`, `6-10` or `10+`). Never returns individuals or contact data. Filters: `blood_group`, `compatible`, `city`. |
| GET | `/search/hospitals/` | Verified hospitals: `id`, `name`, `city`, `address`. Filters `city`, `name`. |

Requests now carry a structured `city` (added in Phase 9 so matching can work by location). Seekers must supply it (`400` if blank, whitespace trimmed); hospital requests take the city from the hospital profile.

Donor side (donor role):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/donors/me/requests/` | Open (`approved` or `matched`) requests in the donor's city whose blood group the donor can safely give to, most urgent first, paginated. Only `id`, `blood_group_name`, `units_required`, `urgency`, `city`, `location`, `hospital_name`, `status`, `created_at`, `my_response`. Patient, requester and contact details are never included. |
| POST | `/donors/me/requests/{id}/respond/` | Body `answer`: `accepted` or `declined`. Must be a match and the request still open. Accepting also requires the donor to be available and eligible today. One row per donor and request; the donor can change their answer while the request is open. **Accepting is consent to share the donor's name and phone with that requester.** |

`GET /donors/me/dashboard/` now includes `matching_requests` (count of the list above).

Requester side (owner or admin; strangers get `404`, other roles `403`):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/requests/{id}/matches/` | Suggested blood banks (top 10 with exact or compatible stock in the request's city, or `?city=`), `exact_stock_units`, `compatible_stock_units`, a banded `available_donors`, and `accepted_donors` (count). No individual donors. |
| GET | `/requests/{id}/responses/` | Donors who accepted, with consented details: `donor_name`, `donor_phone`, `blood_group_name`, `city`. Declined donors are never shown. |

`GET /hospitals/blood-availability/` (Phase 6) still works but `/search/blood/` supersedes it; the frontend now uses the search endpoint.

## Notifications (Phase 10)

In-app only (per Doc.md; email/SMS deferred). Fields: `id`, `type` (`request`/`donation`/`status_change`/`verification`/`alert`), `message`, `related_object_type`, `related_object_id`, `is_read`, `created_at`. Newest first, paginated.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/notifications/`, `/notifications/{id}/` | any user | Own notifications (admin sees everyone's, for oversight; still cannot mark others' read). Filter `?is_read=true` or `?is_read=false`. |
| GET | `/notifications/unread_count/` | any user | `{count}`, own unread only. |
| POST | `/notifications/{id}/read/` | any user | Marks one of the caller's own as read; `404` for anyone else's (including admin). |
| POST | `/notifications/read-all/` | any user | Marks all of the caller's unread as read; `{updated: <n>}`. |

Automatic triggers (fired inside the same transaction as the state change, so they roll back with it):

| Event | Who is notified |
|-------|------------------|
| Blood request status changes | The requester, unless they made the change themselves (e.g. their own cancel). |
| A request is approved | Eligible, available donors in the request's city who can safely give that blood group (capped at 100 to bound bulk sends). |
| A donor accepts a request | The requester, naming the donor. |
| A donation is scheduled | The blood bank. |
| A donation is completed | The donor. |
| A donation is rejected | The donor, with the reason. |
| A hospital or blood bank is verified or unverified | That organisation's account. |

## Admin panel (Phase 12)

Admin-only controls, layered on top of endpoints built in earlier phases.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/` | User management: list/detail. Filters `?role=`, `?is_active=true` or `?is_active=false`, `?search=` (username contains). Never exposes passwords. |
| POST | `/users/{id}/deactivate/`, `/users/{id}/activate/` | Deactivating a user prevents login (`401` on their next login attempt); `400` if the target is yourself or another admin account. Reactivation sends a notification. |
| POST | `/donors/{id}/verify/`, `/donors/{id}/unverify/` | Donor verification, symmetric with hospital/bank verification (Phases 6 and 7). Purely informational for now: no donor action currently checks it. `GET /donors/` also takes `?verified=true` or `?verified=false`. |
| GET | `/inventory/`, `/inventory/transactions/` | Already admin-readable since Phase 7; used here for cross-bank inventory monitoring. |
| GET | `/donations/` | Already admin-readable since Phase 8; used here for cross-bank donation monitoring. |
| GET | `/notifications/` | Already admin-readable since Phase 10. |

Hospital and blood bank verification, and the admin request-status workflow, were already admin panel functionality from Phases 5 to 7.

## Dashboards (Phase 11)

Per-role summary endpoints, all `GET`. Donor and hospital dashboards were introduced in Phases 4 and 6; the three below are new.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/dashboard/` | admin | `total_users`, `users_by_role`, `total_donors`, `total_hospitals`/`verified_hospitals`, `total_bloodbanks`/`verified_bloodbanks`, `request_counts` (every status), `pending_requests`, `completed_requests`, `donation_counts` (every status), `blood_inventory` (usable units per group, all banks, all 8 groups). |
| GET | `/requests/dashboard/` | seeker | `request_counts`, `active_requests` (pending/approved/matched/processing), `recent_requests` (5), `unread_notifications`. Hospitals use their own `/hospitals/me/dashboard/` instead (`403` here). |
| GET | `/bloodbanks/me/dashboard/` | blood bank (any verification state) | `profile`, `stock_by_blood_group`, `expiring_within_7_days` (map of blood_group id to units), `units_collected`/`units_issued`/`units_expired` (all-time, from the ledger), `donation_counts`, `scheduled_donations`, `my_request_counts` (requests this bank fulfilled, by status), `open_requests_for_fulfilment` (unclaimed approved requests, platform-wide), `unread_notifications`. |

## Reference data and admin lookups (Phase 2, permissions updated in Phase 3)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/blood-groups/` | any user | The 8 blood groups. |
| GET | `/users/` | admin | User list (no passwords). |

Read-only admin-only placeholder lists (superseded module by module in later phases): `/notifications/`.
