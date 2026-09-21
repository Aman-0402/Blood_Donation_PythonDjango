# Agent.md — AI Development Progress Log

Running log of what the AI agent has done and what remains, kept in sync with `docs/development-progress.md` (which is the authoritative per-phase record per Doc.md). This file is a quicker top-level glance; `docs/development-progress.md` has full detail per phase (files, tests, commit hashes).

---

## Status: Phase 1 complete. Awaiting approval for Phase 2.

## Completed

### Phase 0 — Requirement Analysis & Planning
- Wrote `docs/project-requirements.md`, `docs/database-design.md`, `docs/development-progress.md`
- Replaced stale `README.md`
- Committed: `9bb4d42`, `1033dbb`. Pushed.

### Phase 1 — Project Setup
- Backend: `backend/` — Django 5.2 project (`config`), venv, apps scaffolded (accounts, donors, hospitals, bloodbanks, donations, bloodrequests, inventory, notifications — empty, no models yet, that's Phase 2), DRF + SimpleJWT + django-cors-headers installed, MySQL connection via PyMySQL (avoids mysqlclient's Windows build toolchain requirement), `.env`/`.env.example`, `/api/health/` verified live against MySQL `blood_db`.
- Frontend: `frontend/` — Vite + React (JS) scaffold, Tailwind CSS v4 (via `@tailwindcss/vite` plugin — v4 replaced the old `postcss`+`init` flow), react-router-dom, axios, base folder structure (`components/ pages/ layouts/ services/ hooks/ context/ routes/ utils/`), `services/api.js` axios client pointed at backend, `pages/Home.jsx` live-checks `/api/health/`.
- Both dev servers verified running together (Vite on 5173 calling Django on 8000, MySQL-backed) — confirmed working end to end.
- Committed: `217acda`. Pushed.

## In Progress / Next Up

- Phase 2 — Database & Backend Foundation: real models (User role field, Donor, Hospital, BloodBank, BloodGroup, Donation, BloodRequest, BloodInventory, Notification), migrations, serializers, admin config.
- Phase 3 — Authentication & Authorization (JWT login/register/refresh, role permissions).
- Phases 4–17 per `Doc.md` — not started.

## Notes / Decisions Made Along the Way

- MySQL: `blood_db`, user `root`, blank password — accepted for local dev, lives in `backend/.env` only (gitignored), `.env.example` has placeholders.
- CSS framework: Tailwind CSS chosen over Bootstrap (user decision).
- README.md was rewritten immediately in Phase 0 instead of waiting for Phase 16, per user decision.
- Backend uses PyMySQL instead of `mysqlclient` (pure-Python driver, no Windows build tools needed) — functionally equivalent DB driver choice, not an architecture change.
