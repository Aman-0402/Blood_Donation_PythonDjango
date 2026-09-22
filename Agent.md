# Agent.md — AI Development Progress Log

Quick top-level view of what the AI agent has done and what remains. `docs/development-progress.md` is the authoritative per-phase record (files, tests, commit hashes, issues).

## Current status

Phase 13 complete (user said "start" after Phase 12, taken as the next phase in sequence). Phases 14-17 not approved yet.

## Completed

- **Phase 0 — Requirements & planning.** docs/project-requirements.md, database-design.md, development-progress.md; README replaced.
- **Phase 1 — Project setup.** Django 5.2 + DRF + SimpleJWT + CORS, MySQL via PyMySQL; Vite + React + Tailwind v4 + Router + Axios; `.env`/`.env.example`.
- **Phase 2 — Database foundation.** Custom User (role), seeded BloodGroup, Donor/Hospital/BloodBank/BloodInventory/Donation/BloodRequest/Notification models with validation, migrations, admin, serializers, admin-only read APIs. `blood_db` recreated once (held only default tables) to adopt the custom User model.
- **Phase 3 — Auth.** Register/login/refresh/logout/me/change-password, token blacklist, role permission classes, frontend auth context + protected routes + auto-refresh. 72 backend tests, live smoke test passed, frontend lint/build clean (not browser-tested).

- **Phase 4 — Donor module.** Donor profile/availability/eligibility/history/dashboard APIs + frontend pages, `ModelCleanMixin` for server-side validation, pagination, configurable eligibility rules (assumed 18-65, 90 days). 102 backend tests, live smoke test passed, frontend lint/build clean.

- **Phase 5 — Blood requests.** Create/edit/cancel, strict admin status workflow with audit history, owner-scoped access, hospital verification gate, frontend list/form/detail. 137 backend tests, live smoke test passed (it caught and fixed a 400-vs-403 ordering bug).

- **Phase 6 — Hospital module.** Profile, admin verification, dashboard, verified-only availability search, reusable expired-aware stock service, frontend pages. 171 backend tests, live smoke test passed.

- **Phase 7 — Blood bank module.** Bank profile + verification, ledger-backed transaction-safe inventory (collect, issue FIFO, expire, adjust), bank request fulfilment (accept/dispatch/complete/release) with patient-data privacy, `expire_blood` command, frontend pages. 223 backend tests incl. real-thread concurrency tests, live smoke test passed.

- **Phase 8 — Donations.** Donors schedule/cancel, banks complete/reject; completion atomically updates status, inventory (+ledger link) and donor history; eligibility judged on donation date; bank directory; frontend pages. 261 backend tests incl. real-thread double-complete test, live smoke test passed.

- **Phase 9 — Search and matching.** ABO/Rh compatibility, search API (blood, donors as banded counts, hospitals), consent-based donor responses, per-request matches, structured request city, frontend search and donor request pages. 312 backend tests, live smoke test passed.

- **Phase 10 — Notifications.** In-app notification API (list/unread_count/mark read/mark all), triggers on request status change, donor accept, donation schedule/complete/reject, org verification. UI upgrade: shared 1450px container, sticky header with notification bell, responsive drawer sidebar. 331 backend tests, live smoke test passed. Also fixed a `transaction.on_commit`-in-`TestCase` bug found by the test run.

- **Phase 11 — Dashboards.** Admin dashboard (counts across users/donors/hospitals/banks/requests/donations/inventory), seeker dashboard, blood bank dashboard (ledger-derived collected/issued/expired). 340 backend tests, live smoke test passed.

- **Phase 12 — Admin panel.** User management (list/filter/deactivate/activate with self- and admin-lockout guards), donor verification (parity with hospital/bank), inventory and donation monitoring pages, generalized `AdminVerification` component. 352 backend tests, live smoke test passed.

- **Phase 13 — Reports & analytics.** Admin-only donation/request/inventory reports, computed live. Three charts (dataviz-skill-compliant fixed palette, validated) plus stat tiles — kept small per Doc.md's "don't overload dashboards" instruction. 362 backend tests, live smoke test passed.

## In progress / next

- Phases 14 to 17: not approved yet, ask before starting (14 UI/UX refinement, 15 testing and security, 16 docs, 17 final review)
- Open item: hospital "manage authorized staff" (Doc.md 3.4) is not covered by any phase

## Dev tooling

- `python manage.py seed_demo_data` — seeds 1000 random Indian demo users (700 donors, 150 seekers, 75 hospitals, 75 blood banks) with profiles, ~300 donations (recent ones via the real schedule/complete flow, older months backfilled directly since the live API can't backdate bookings), ~200 blood requests, and inventory. Every username starts with `demo_`; all share password `Demo@12345`. `--flush` deletes them; `--flush --no-reseed` just deletes. Not run automatically anywhere. Local dev DB only — never run against anything real.

## Decisions and assumptions

- MySQL `blood_db`, user `root`, blank password: local dev only, in gitignored `backend/.env`.
- Tailwind CSS chosen over Bootstrap (user decision).
- PyMySQL instead of mysqlclient (no Windows build tools needed).
- Doc.md RULE 7 (no Co-authored-by trailer) is followed for every commit; it overrides any default attribution.
- Verification lives on `User.is_verified` only.
- Login throttling and JWT-in-localStorage risk deferred to Phase 15 security review.
