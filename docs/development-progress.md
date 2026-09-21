# Development Progress

Tracks each completed phase per Doc.md workflow.

---

## Phase 0 — Requirement Analysis & Planning

Status: Completed
Date: 2026-09-21
Completed:
- Inspected repo (empty except Doc.md, README, .vscode)
- Confirmed tool availability: Python 3.10.11, Node 22.23.2, npm 10.9.8, MySQL 8.0.30
- Resolved open questions: Tailwind CSS chosen, blank MySQL root password accepted (local dev, .env only), README overwritten now
- Wrote docs/project-requirements.md
- Wrote docs/database-design.md
- Overwrote stale README.md

Files changed:
- docs/project-requirements.md (new)
- docs/database-design.md (new)
- docs/development-progress.md (new)
- README.md (rewritten)

Tests:
- N/A (docs-only phase)

Git commit: 9bb4d42bb63a21780605bc0a9a8880f864648a5c
Git push: Successful

Issues: none

---

## Phase 1 — Project Setup

Status: Completed
Date: 2026-09-21
Completed:
- Backend: Django 5.2 project (`config`) + venv in `backend/`, apps scaffolded (accounts, donors, hospitals, bloodbanks, donations, bloodrequests, inventory, notifications — no models yet, that's Phase 2), DRF, SimpleJWT, django-cors-headers installed, MySQL connection configured via PyMySQL, `.env`/`.env.example`, `/api/health/` endpoint
- Frontend: Vite + React (JS) in `frontend/`, Tailwind CSS v4 (`@tailwindcss/vite`), react-router-dom, axios, base folder structure (components/pages/layouts/services/hooks/context/routes/utils), `services/api.js` axios client, `pages/Home.jsx` calling backend health check
- `.gitignore` added (venv, node_modules, .env, db.sqlite3, dist excluded)
- `Agent.md` progress tracker added

Files changed:
- backend/ (Django project + 8 empty apps + config)
- frontend/ (Vite React project + base structure)
- .gitignore (new)
- Agent.md (new)

Testing:
- `python manage.py check` — no issues
- `python manage.py migrate` — applied against live MySQL `blood_db` successfully
- `GET /api/health/` → `{"status": "ok"}` while Django server running
- `npm run build` — frontend builds clean, Tailwind compiles
- Both dev servers (Vite :5173, Django :8000) run concurrently; frontend confirmed reaching backend health check live

Git commit: 217acdae86a9855d9647accec6e22056b5ddd4ec
Git push: Successful

Issues: none

Notes:
- Used PyMySQL instead of `mysqlclient` (pure-Python driver, avoids Windows C build toolchain) — functionally equivalent, no architecture impact
- Tailwind v4 uses `@tailwindcss/vite` plugin, not the old `postcss.config.js` + `tailwind.config.js` init flow (v4 breaking change)

---

## Phase 2 — Database & Backend Foundation

Status: Completed
Date: 2026-09-22
Completed:
- Custom `accounts.User` (role, phone, is_verified, unique email) via `AUTH_USER_MODEL`; `BloodGroup` table seeded with 8 groups by data migration
- Models: Donor, Hospital, BloodBank, BloodInventory, Donation, BloodRequest, Notification, with `clean()` validation and PROTECT/CASCADE policy
- Migrations created and applied to MySQL `blood_db`
- Django admin registered for every model
- DRF serializers + read-only, admin-only viewsets + routes: `/api/users/ /blood-groups/ /donors/ /hospitals/ /bloodbanks/ /inventory/ /donations/ /requests/ /notifications/`
- `docs/database-design.md` updated to the as-built design

Files changed:
- backend/apps/*/ (models, admin, serializers, views, urls, tests, migrations), backend/apps/testing.py, backend/config/settings.py, backend/config/urls.py
- docs/database-design.md, docs/development-progress.md, Agent.md

Tests:
- `manage.py check` clean; `makemigrations --check` shows no drift
- `manage.py test`: 43 tests, all pass (model validation, relationships, unique constraints, PROTECT/CASCADE, seed data, API 401/403/200/405, password never exposed)

Git commit: 9cf8a2ea705f9c40b97f1e57b7a01738bd2992d8
Git push: Successful

Issues / decisions:
- Swapping to a custom User model required a fresh DB. `blood_db` held only default Django tables and zero users, so it was dropped and recreated before migrating.
- Deviations from the Phase 0 draft (recorded in database-design.md): verification lives only on User; donor/hospital/bank use `city` + `address`; donation `quantity` is in units; `Role` is a choices field, not a table.
- `clean()` is not invoked by bare `.save()`; write APIs in later phases must enforce it.

---

## Phase 3 — Authentication & Authorization

Status: Completed
Date: 2026-09-22
Completed:
- Backend: register, login, refresh (rotating, blacklisted), logout, me (GET/PATCH), change-password under `/api/auth/`; SimpleJWT blacklist app; role claim in access token
- Role-based permission classes (`IsAdminRole`, `IsDonor`, `IsSeeker`, `IsHospital`, `IsBloodBank`); existing admin lists moved from `is_staff` to `role == admin`; `/api/blood-groups/` opened to any authenticated user
- Self-registration limited to donor/seeker/hospital/bloodbank; privilege fields ignored
- Frontend: token storage, axios auto-refresh interceptor (single-flight), AuthContext/useAuth, Login and Register pages, role-protected routes, dashboard layout shell, shared Alert/Button/FormField components
- Fixed a Phase 2 flaw found by the test run: notification ordering tie on identical timestamps (added `-id` tiebreaker, migration `notifications.0002`)
- Added `docs/api-documentation.md`

Files changed:
- backend/apps/accounts/{permissions,serializers,views,urls}.py, test_auth.py, test_api.py; backend/config/{settings,urls}.py; backend/apps/*/views.py (permission swap); notifications model + migration
- frontend/src/{services,context,hooks,routes,layouts,components,pages,utils}
- docs/api-documentation.md, docs/development-progress.md, Agent.md

Tests:
- Backend `manage.py test`: 72 tests pass. Covers valid/invalid login, inactive user, unauthorized access, role restrictions (incl. `is_staff` not granting admin), token expiry, refresh rotation and reuse rejection, logout blacklisting (and cross-user rejection), refresh token rejected as access token, registration hardening (no admin, no privilege fields, weak/duplicate credentials), password change
- Live smoke test against running Django + MySQL: register, login, me, 401 without token, 403 for donor on admin endpoint, 401 bad login, logout 205, refresh after logout 401; CORS allows only `http://localhost:5173`
- Frontend: `npm run lint` clean, `npm run build` succeeds. Not exercised in a real browser (no browser automation available in this environment).

Git commit: 5dbe5e7067face79cbd3f5c082ff3159ec6ae93f
Git push: Successful

Issues / decisions:
- No login throttling yet; scheduled for Phase 15 security review.
- JWTs are kept in `localStorage` (standard SPA approach, exposed to XSS). To be reviewed in Phase 15.
- Unverified accounts can log in; verification gates specific actions in later phases (hospital/bank actions), not login.

---

## Phase 4 — Donor Module

Status: Completed
Date: 2026-09-22
Completed:
- Backend: donor profile create/read/update (`/donors/`, `/donors/me/`), donation history, donor dashboard, admin list/retrieve; donors cannot see each other; email/phone never exposed
- Server-side validation via new `ModelCleanMixin` (`apps/validation.py`) so API writes reuse model `clean()` rules; blood group locked once donations exist; owner cannot be spoofed
- Eligibility engine (`donors/eligibility.py`): age range and minimum interval since last donation, configurable through env settings
- Global pagination (page size 20); `TIME_ZONE` now configurable (`DJANGO_TIME_ZONE`)
- Frontend (Axios services): donor dashboard, profile create/edit form with availability toggle and eligibility banner, paginated donation history; shared StatCard/StatusBadge components
- API docs updated

Files changed:
- backend/apps/donors/{views,serializers,eligibility,test_api}.py, backend/apps/validation.py, backend/apps/donations/serializers.py, backend/apps/accounts/{views,test_api}.py, backend/apps/testing.py, backend/config/settings.py, backend/.env.example
- frontend/src/pages/donor/*, services/{donors,reference}.js, hooks/useBloodGroups.js, components/{StatCard,StatusBadge}.jsx, layouts/navConfig.js, routes/AppRoutes.jsx
- docs/api-documentation.md, docs/development-progress.md, Agent.md

Tests:
- Backend: 102 tests pass (30 new donor API tests: role gating, create/duplicate/spoof, validation matrix, PUT/PATCH, blood-group lock, eligibility incl. age boundaries/interval/configurability/completed-vs-scheduled donations, history isolation, dashboard counts, admin vs donor access, privacy)
- Live smoke test against running Django + MySQL: full donor workflow passed (register, 404 before profile, validation rejects, create, duplicate rejected, availability toggle, dashboard, history, seeker gets 403); test users removed afterwards
- Frontend: lint clean, build succeeds. Not exercised in a real browser (no browser automation available here), so UI behavior is verified by build and API-level tests only.

Git commit: b2931c31ce37ebc8bc1b848a9322e5e487bf29bd
Git push: Successful

Issues / decisions (assumptions to confirm):
- Eligibility defaults (age 18 to 65, 90-day interval) are my assumptions, not from Doc.md; they are env-configurable.
- Test bug found and fixed: tests used the machine's local date while the app uses the configured timezone (UTC), causing an off-by-one age.
- "Active requests" on the donor dashboard is deferred: it needs request-to-donor matching (Phase 9) and request data (Phase 5).
- Doc.md's donor "accept/decline requests" also depends on matching and is deferred to Phase 9.

---

## Phase 5 — Blood Request Module

Status: Completed
Date: 2026-09-22
Completed:
- Backend: create / list / retrieve / edit / cancel requests, admin status workflow with a strict transition map, per-request audit history; requests cannot be deleted
- Access rules: seekers and hospitals see only their own requests, admins see all, other roles get 403, strangers get 404; hospital requests need a hospital profile and a verified account
- Server-controlled fields (`requester`, `hospital`, `status`, `fulfilled_by_bloodbank`) cannot be set by clients; edits only while `pending`
- Status changes run in a row-locked transaction so concurrent changes cannot both succeed (`bloodrequests/workflow.py`)
- Model additions: `contact_phone`, `notes`, `RequestStatusHistory` (migration `bloodrequests.0002`); Django admin shows history inline
- Frontend (Axios): request list with status filter and pagination, create/edit form, detail page with history timeline, owner cancel, admin status buttons with note; shared by seeker, hospital and admin routes
- API and database docs updated

Files changed:
- backend/apps/bloodrequests/{models,serializers,views,workflow,admin,test_api}.py + migration, backend/apps/accounts/test_api.py
- frontend/src/pages/requests/*, services/requests.js, layouts/navConfig.js, routes/AppRoutes.jsx
- docs/api-documentation.md, docs/database-design.md, docs/development-progress.md, Agent.md

Tests:
- Backend: 137 tests pass (35 new request tests: create/validation matrix, server-controlled fields, hospital verified/unverified/no-profile, list scoping and filters, ordering, 404 for strangers, edit rules, cancel rules per state, full admin happy path with history, invalid jumps, terminal states, role gating, workflow unit tests incl. repeated-transition rejection)
- Live smoke test against running Django + MySQL: 14 checks passed (create, validation, unverified hospital 403, stranger 404, edit, admin approve, invalid jump 400, edit-after-approval 400, owner cancel, final state, history trail); test data removed afterwards
- The live test caught a real ordering bug (unverified hospital without a profile got 400 instead of 403); fixed by checking verification before validation, with a regression test
- Frontend: lint clean, build succeeds. Not exercised in a real browser.

Git commit: a8d6c6ed791c24c89282945d52fcd6152483381f
Git push: Successful

Issues / decisions:
- Cap of 100 units per request is my assumption (guard against nonsense values); easy to change in `bloodrequests/models.py`.
- Only admins move requests forward for now. Blood banks get processing/completion in Phase 7; automatic matching in Phase 9.
- Notifications on request events are not sent yet (Phase 10).

---

## Phase 6 — Hospital Module

Status: Completed
Date: 2026-09-22
Completed:
- Backend: hospital profile create/read/update, admin verification (verify/unverify) and admin browse with a verified filter, hospital dashboard, blood availability search
- Verification gate: unverified hospitals cannot create requests (Phase 5) or search availability; admin unverify takes effect immediately
- Reusable stock service (`inventory/services.py`): usable stock excludes expired units and non-available statuses, sums batches, supports blood group and city filters
- Availability responses contain only bank name, city, blood group and units (no personal data)
- Frontend (Axios): hospital dashboard (verification banner, request stats, stock by blood group, recent requests), profile form, availability search, admin hospital verification page; hospital nav and routes reuse the Phase 5 request pages
- API docs updated

Files changed:
- backend/apps/hospitals/{views,serializers,test_api}.py, backend/apps/inventory/{services,test_services}.py, backend/apps/testing.py, backend/apps/accounts/test_api.py
- frontend/src/pages/hospital/*, pages/admin/AdminHospitals.jsx, services/hospitals.js, layouts/navConfig.js, routes/AppRoutes.jsx
- docs/api-documentation.md, docs/development-progress.md, Agent.md

Tests:
- Backend: 171 tests pass (34 new: profile role gating/duplicate/validation/spoofing/license uniqueness, verification permissions and end-to-end request gating, dashboard counts/isolation/stock/notifications, availability filters/expiry/permissions/params/privacy, stock service boundaries)
- Live smoke test against running Django + MySQL: 16 checks passed, including expired inventory being excluded; test data removed afterwards
- Frontend: lint clean, build succeeds. Not exercised in a real browser.

Git commit: cecd7b05e5409736fe109ad0f74363b797fd850a
Git push: Successful

Issues / decisions:
- Doc.md section 3.4 lists "manage authorized staff" for hospitals, but no phase covers it. Not implemented; needs a decision (likely a future addition).
- Availability search requires a verified hospital. That restriction is my choice, consistent with the request gate.
- Test-only finding: `force_authenticate` reuses a stale user object, so tests that change verification mid-test must re-fetch the user.

---

## Phase 7 — Blood Bank Module

Status: Completed
Date: 2026-09-22
Completed:
- Blood bank profile, `me`, admin verification and browse (same pattern as hospitals); unverified banks can read but not change stock or fulfil requests
- Transaction-safe inventory (`inventory/services.py`): record collection, issue units (oldest expiry first, all-or-nothing, row-locked), expire lapsed stock, adjust a batch (reason required, zero discards it), usable-stock, summary and expiring-soon queries
- Append-only ledger `InventoryTransaction` for full inventory history (collection, issue, expired, adjustment), with API and read-only Django admin
- Request fulfilment by banks (`bloodrequests/fulfillment.py`): accept (one winner under concurrency), dispatch (issues stock and moves to processing atomically), complete, release
- Privacy: banks see only approved unassigned requests plus their own, and patient/requester details stay hidden until they own the request
- Management command `expire_blood` for a daily cron
- Frontend (Axios): bank stock overview, profile, inventory (add units, filter, remove expired, adjust), issue form, ledger history, request pages with bank actions; admin verification page generalised for hospitals and banks; shared `OrgProfileForm`
- API and database docs updated

Files changed:
- backend/apps/bloodbanks/{access,serializers,views,test_api}.py, backend/apps/inventory/{models,services,serializers,views,urls,admin,test_api,test_concurrency,test_services}.py + migration + management command, backend/apps/bloodrequests/{workflow,fulfillment,serializers,views,test_fulfillment,test_api}.py, backend/apps/accounts/test_api.py, backend/config/settings.py, backend/.env.example
- frontend/src/pages/bank/*, pages/admin/AdminVerification.jsx (renamed from AdminHospitals), pages/requests/*, components/OrgProfileForm.jsx, services/{bloodbanks,inventory,requests}.js, layouts/navConfig.js, routes/AppRoutes.jsx
- docs/*, Agent.md

Tests:
- Backend: 223 tests pass (52 new bank/inventory/fulfilment tests). Includes two real-thread concurrency tests on MySQL: four parallel issues against 10 units succeed exactly three times with no oversell, and three banks racing to accept one request produce exactly one winner
- Live smoke test against running Django + MySQL: 27 checks passed across the whole path (verify bank, collect, adjust, request approve, accept, dispatch, complete, ledger links, walk-in issue, expire sweep); test data removed afterwards
- Frontend: lint clean, build succeeds. Not exercised in a real browser.

Git commit: 07a96f763d72c08109c08abfe88ed364db07a7b6
Git push: Successful

Issues / decisions:
- Caught during development: a viewset method named `dispatch` would have replaced DRF's request dispatcher; the action is `dispatch_blood` with URL `/dispatch/`.
- Accepting a request does not reserve stock; dispatch re-checks and fails cleanly (no partial change) if stock vanished. Reservation could be added later if needed.
- Added `matched -> approved` to the request workflow so a bank can release a request it cannot fulfil.
- Admins can still move requests through statuses manually (Phase 5); a manual `matched` without a bank has no assigned bank to dispatch it.
- Shelf life default of 35 days, 1000-unit operation cap and the 7-day "expiring soon" window are my assumptions.
- Donations are not yet linked to inventory: Phase 8 will call `record_collection` when a donation completes.
- Bank "dashboard" statistics belong to Phase 11; Phase 7 provides the stock overview and ledger instead.

---

## Phase 8 — Blood Donation Module

Status: Completed
Date: 2026-09-22
Completed:
- Backend: donors schedule donations with a verified blood bank; donors cancel; banks complete or reject; role-scoped list/detail (donor own, bank own, admin all)
- Scheduling rules enforced on the server: date window, verified bank, donor available, one scheduled donation at a time, eligibility judged on the donation date (reuses the Phase 4 engine)
- Completion is one atomic step (`donations/services.py`): status, new inventory batch plus a ledger entry linked to the donation, and the donor's `last_donation_date` (never moved backwards); any failure rolls everything back; row locks make a double complete safe
- Donor history and dashboard update automatically from completed donations; eligibility resets for the donation interval
- Bank directory endpoint (verified banks, organisation details only) for the donor's bank picker
- Privacy: only the booked bank (and admin) sees donor name and phone
- Frontend (Axios): donor schedule page and cancel from history; bank donation queue with complete (units) and reject (reason); nav and routes
- API and database docs updated

Files changed:
- backend/apps/donations/{models,services,serializers,views,test_api,test_concurrency}.py + migration, backend/apps/inventory/{models,services}.py + migration, backend/apps/bloodbanks/views.py, backend/apps/accounts/test_api.py, backend/config/settings.py, backend/.env.example
- frontend/src/pages/donor/{ScheduleDonation,DonorDonations}.jsx, pages/bank/BankDonations.jsx, services/donations.js, layouts/navConfig.js, routes/AppRoutes.jsx
- docs/*, Agent.md

Tests:
- Backend: 261 tests pass (38 new: scheduling validation matrix, eligibility on the donation date, one-at-a-time rule, spoofing, cancel/complete/reject state rules, cross-bank isolation, privacy of contact fields, completion updating inventory + ledger + donor history + eligibility, full rollback on failure, directory) plus a real-thread test where two simultaneous completes add stock exactly once
- Live smoke test against running Django + MySQL: 30 checks passed across schedule, complete, ledger link, eligibility lockout, rebook after interval, cancel and reject; test data removed afterwards
- Frontend: lint clean, build succeeds. Not exercised in a real browser.

Git commit: 5ab5834646bd16fab15077330ae3f83f35bc25bc
Git push: Successful

Issues / decisions:
- Assumptions (configurable or easy to change): quantity defaults to 1 unit and is set by the bank on completion (max 10); bookings up to 90 days ahead; at most one scheduled donation per donor.
- Banks cannot record walk-in donations for donors who did not book (would need a privacy-safe donor lookup, which belongs with Phase 9).
- A donation can only be completed on or after its date. A booking left uncompleted past the shelf life cannot be completed (it fails cleanly); the bank should reject it.
- Blood group cannot change on the donor profile once donations exist (Phase 4 rule), which keeps donation blood groups consistent.
- Notifications for scheduling/completion are not sent yet (Phase 10).
- Smoke-script slip (not a product bug): tried booking day 91, beyond the 90-day horizon; day 90 is the first eligible date after a donation and is allowed.

---

## Phase 9 — Blood Search & Matching

Status: Completed
Date: 2026-09-22
Completed:
- ABO/Rh compatibility engine (`accounts/compatibility.py`), verified against the full 8x8 transfusion table; exact matches always rank before compatible ones
- Search API under `/api/search/`: blood availability (group, compatible groups, city, bank id/name, minimum units), donor availability as banded counts, hospital directory; only verified banks' usable stock; hospitals and banks must be verified
- Database-level eligible-donor query (`donors/eligibility.py: eligible_donors`) so search does not loop per donor; tests cross-check it against the Python rules on leap-day and boundary dates
- Donor matching: donors see compatible open requests in their city without any patient details and can accept or decline; accepting requires availability and eligibility and is explicit consent to share name and phone with that requester only
- Requester side: per-request matches (banks by fit, banded donor count) and the list of accepting donors; donor dashboard shows matching requests (closes the item deferred from Phase 4)
- Requests gained a structured `city` (required for seekers, from the profile for hospitals); the old hospital availability page was replaced by a shared search page
- Frontend (Axios): search page with three tabs, donor "requests near you" page with consent notice, match and offers panel on request detail, city field on the request form
- API and database docs updated

Files changed:
- backend/apps/accounts/compatibility.py, backend/apps/search/*, backend/apps/bloodrequests/{models,serializers,views,matching,test_matching,tests,test_api}.py + migration, backend/apps/donors/{eligibility,views,test_eligible_query}.py, backend/apps/inventory/services.py, backend/apps/accounts/test_compatibility.py, backend/config/urls.py
- frontend/src/pages/search/SearchPage.jsx, pages/donor/DonorRequests.jsx, components/MatchPanel.jsx, services/search.js, pages/requests/{RequestDetail,RequestForm}.jsx, pages/donor/DonorDashboard.jsx, layouts/navConfig.js, routes/AppRoutes.jsx (BloodAvailability page removed)
- docs/*, Agent.md

Tests:
- Backend: 312 tests pass in the full run (about 51 new: compatibility matrix and properties, DB-vs-Python eligibility on four calendar scenarios, search permissions/ranking/filters/privacy/verified-only/expired-hidden, banded counts, donor request visibility/urgency ordering/hidden fields, respond rules incl. eligibility and closed requests, requester offers with consent, matches, request city rules)
- Live smoke test against running Django + MySQL: 32 checks passed (search, banding, city requirement, donor visibility, consent-based offers, matches without leaking phone numbers, closed request rejects responses); test data removed afterwards
- Frontend: lint clean, build succeeds. Not exercised in a real browser.
- The full run caught a real regression: a Phase 2 model test built a seeker request without a city; fixed the fixture and added an explicit city-rule test.

Git commit: see next entry
Git push: see next entry

Issues / decisions:
- Privacy choices (mine, worth reviewing): donor search only returns banded counts; contact details are shared only after a donor explicitly accepts a specific request; banks never get donor search.
- Phase 5 gap closed: matching by location needed a structured city; existing requests keep an empty city and will not match donors until edited.
- `GET /hospitals/blood-availability/` (Phase 6) is kept but superseded by `/search/blood/`; consider removing it later to avoid duplication.
- Donors are matched by exact city name (case-insensitive), not by distance; geographic radius search would need coordinates and is out of scope.
- Notifying matching donors when a request is approved belongs to Phase 10.
- Smoke-script slip (not a product bug): expected 3 to 5 compatible donors when only 2 existed.

---
