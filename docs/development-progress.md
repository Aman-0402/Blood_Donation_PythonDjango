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

Git commit: see git log (`feat: add core models, migrations and base API`)
Git push: see below

Issues / decisions:
- Swapping to a custom User model required a fresh DB. `blood_db` held only default Django tables and zero users, so it was dropped and recreated before migrating.
- Deviations from the Phase 0 draft (recorded in database-design.md): verification lives only on User; donor/hospital/bank use `city` + `address`; donation `quantity` is in units; `Role` is a choices field, not a table.
- `clean()` is not invoked by bare `.save()`; write APIs in later phases must enforce it.

---
