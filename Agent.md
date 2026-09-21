# Agent.md — AI Development Progress Log

Quick top-level view of what the AI agent has done and what remains. `docs/development-progress.md` is the authoritative per-phase record (files, tests, commit hashes, issues).

## Current status

Phase 8 complete. User approved Phases 3 to 6, then Phases 7 to 9, each committed and pushed separately. Phase 9 is next.

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

## In progress / next

- Phase 9: blood search and matching (approved)
- Phases 10 to 17: not approved yet, ask before starting
- Open item: hospital "manage authorized staff" (Doc.md 3.4) is not covered by any phase

## Decisions and assumptions

- MySQL `blood_db`, user `root`, blank password: local dev only, in gitignored `backend/.env`.
- Tailwind CSS chosen over Bootstrap (user decision).
- PyMySQL instead of mysqlclient (no Windows build tools needed).
- Doc.md RULE 7 (no Co-authored-by trailer) is followed for every commit; it overrides any default attribution.
- Verification lives on `User.is_verified` only.
- Login throttling and JWT-in-localStorage risk deferred to Phase 15 security review.
