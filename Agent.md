# Agent.md — AI Development Progress Log

Quick top-level view of what the AI agent has done and what remains. `docs/development-progress.md` is the authoritative per-phase record (files, tests, commit hashes, issues).

## Current status

Phase 3 complete. User approved Phases 3 to 6 in one go, each committed and pushed separately. Phase 4 is next.

## Completed

- **Phase 0 — Requirements & planning.** docs/project-requirements.md, database-design.md, development-progress.md; README replaced.
- **Phase 1 — Project setup.** Django 5.2 + DRF + SimpleJWT + CORS, MySQL via PyMySQL; Vite + React + Tailwind v4 + Router + Axios; `.env`/`.env.example`.
- **Phase 2 — Database foundation.** Custom User (role), seeded BloodGroup, Donor/Hospital/BloodBank/BloodInventory/Donation/BloodRequest/Notification models with validation, migrations, admin, serializers, admin-only read APIs. `blood_db` recreated once (held only default tables) to adopt the custom User model.
- **Phase 3 — Auth.** Register/login/refresh/logout/me/change-password, token blacklist, role permission classes, frontend auth context + protected routes + auto-refresh. 72 backend tests, live smoke test passed, frontend lint/build clean (not browser-tested).

## In progress / next

- Phase 4: donor module (profile, availability, eligibility, history, dashboard)
- Phase 5: blood request module (create/update/cancel, status workflow, history)
- Phase 6: hospital module (profile, verification, dashboard, availability search)
- Phases 7 to 17: not approved yet, ask before starting

## Decisions and assumptions

- MySQL `blood_db`, user `root`, blank password: local dev only, in gitignored `backend/.env`.
- Tailwind CSS chosen over Bootstrap (user decision).
- PyMySQL instead of mysqlclient (no Windows build tools needed).
- Doc.md RULE 7 (no Co-authored-by trailer) is followed for every commit; it overrides any default attribution.
- Verification lives on `User.is_verified` only.
- Login throttling and JWT-in-localStorage risk deferred to Phase 15 security review.
