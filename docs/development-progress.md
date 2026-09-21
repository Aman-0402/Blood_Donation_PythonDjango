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

Git commit: see next entry
Git push: see next entry

Issues / decisions (assumptions to confirm):
- Eligibility defaults (age 18 to 65, 90-day interval) are my assumptions, not from Doc.md; they are env-configurable.
- Test bug found and fixed: tests used the machine's local date while the app uses the configured timezone (UTC), causing an off-by-one age.
- "Active requests" on the donor dashboard is deferred: it needs request-to-donor matching (Phase 9) and request data (Phase 5).
- Doc.md's donor "accept/decline requests" also depends on matching and is deferred to Phase 9.

---
