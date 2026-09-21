# Project Requirements — Blood Donation Management System

## 1. Overview

Centralized platform connecting donors, blood seekers, hospitals, and blood banks, administered by system admins. Built as a production-style system with role-based access, real API-backed workflows, and inventory-safe transactions.

## 2. Tech Stack

- **Frontend**: React.js, Vite, JavaScript, React Router, Axios, Tailwind CSS
- **Backend**: Python, Django, Django REST Framework, JWT auth (SimpleJWT)
- **Database**: MySQL (`blood_db`)
- **Version control**: Git / GitHub

## 3. User Roles

| Role | Summary |
|------|---------|
| Admin | Full system management, verification, reports |
| Donor | Profile, availability, donation history, respond to requests |
| Blood Seeker / Patient | Search blood, create/track requests |
| Hospital | Manage requirements, requests, staff |
| Blood Bank | Manage inventory, collection, dispatch, expiry |

Full per-role capability list: see Doc.md §3.

## 4. Functional Requirements

- FR1: User registration/login/logout with JWT, role assigned at signup or by admin.
- FR2: Role-based dashboard content and API access (enforced server-side, not just UI).
- FR3: Donor CRUD profile including blood group, location, availability, eligibility fields.
- FR4: Blood request lifecycle: create → pending → approved/matched → processing → completed/cancelled/rejected.
- FR5: Blood bank inventory CRUD with unit-level tracking (collection date, expiry date, status).
- FR6: Donation record lifecycle: scheduled → completed/cancelled/rejected; auto-updates donor history and inventory on completion.
- FR7: Search/matching by blood group, location, availability, blood bank, hospital — without exposing unnecessary personal data of donors to searchers.
- FR8: In-app notifications for request/donation/status/account-verification events.
- FR9: Role-specific dashboards with aggregate counts (users, donors, hospitals, requests, inventory).
- FR10: Admin verification workflow for donor/hospital/blood bank accounts.
- FR11: Reports: donation stats, inventory stats, request stats, blood-group breakdowns, monthly trends.

## 5. Non-Functional Requirements

- NFR1: Backend enforces all business rules and permissions; frontend validation is UX-only (RULE 14).
- NFR2: React never talks to MySQL directly — always via DRF REST API (RULE 15).
- NFR3: Inventory updates must be transaction-safe (avoid race conditions on concurrent donation/issue/expiry updates).
- NFR4: No secrets committed; `.env` + `.env.example` pattern.
- NFR5: Responsive UI (mobile + desktop).
- NFR6: API input validation via DRF serializers; SQL injection / XSS protection by default via ORM + DRF + React escaping.
- NFR7: Passwords hashed (Django default PBKDF2); JWT access + refresh token flow.

## 6. Blood Groups Supported

A+, A-, B+, B-, AB+, AB-, O+, O- — modeled as a configurable table (`BloodGroup`), not hardcoded, so new types/config can be added later.

## 7. Edge Cases Identified

- Donor marked unavailable should not appear in search/matching results.
- Blood request for a group with zero inventory should still be creatable (status stays pending/unmatched) — creation isn't blocked by current stock.
- Expired inventory units must be excluded from available-stock calculations, not just flagged.
- Donation completion must only decrement/increment inventory once (idempotent status transition, no double-counting on retry).
- Hospital/blood bank/donor accounts start unverified; unverified accounts have restricted actions until admin approval.
- A request's urgency/status changes must be auditable (who changed it, when) for reporting.
- Notification records must not leak other users' personal data in payload.

## 8. Out of Scope (this phase / unless requested later)

- Payment processing
- SMS/email delivery (in-app notifications only for now, per Doc.md §Phase 10)
- Microservices split
- AI-based matching

## 9. Frontend Pages (initial plan)

- Public: Landing, Login, Register
- Shared: Notifications
- Admin: Dashboard, Users, Donors, Hospitals, Blood Banks, Requests, Inventory, Reports
- Donor: Dashboard, Profile, Donation History, Requests feed
- Seeker/Patient: Dashboard, Search Blood, My Requests, Request Detail
- Hospital: Dashboard, Profile, Requirements, Requests, Blood Availability Search
- Blood Bank: Dashboard, Inventory, Collections, Dispatch, Expired Units

## 10. API Plan (high-level, detailed per-phase)

- `/api/auth/` — register, login, refresh, logout
- `/api/users/` — admin user management
- `/api/donors/` — donor profile CRUD
- `/api/hospitals/` — hospital profile CRUD
- `/api/bloodbanks/` — blood bank profile CRUD
- `/api/inventory/` — inventory CRUD (blood bank scoped)
- `/api/donations/` — donation records
- `/api/requests/` — blood requests
- `/api/search/` — blood/donor/bank search
- `/api/notifications/` — notification list/read
- `/api/reports/` — aggregate stats

Exact endpoints/serializers finalized per-phase as each module is built.
