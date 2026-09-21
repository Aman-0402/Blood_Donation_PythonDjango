# Blood Donation Management System

## React + Django — AI Development Master Prompt & Project Documentation

---

# 1. Project Overview

Build a complete **Blood Donation Management System** using:

### Frontend

* React.js
* Vite
* JavaScript
* React Router
* Axios
* Bootstrap / Tailwind CSS
* Responsive UI

### Backend

* Python
* Django
* Django REST Framework
* JWT Authentication
* REST APIs

### Database

* MySQL

### Version Control

* Git
* GitHub

---

# 2. Main Objective

The system should provide a centralized platform where:

* Donors can register and manage their profiles.
* Blood seekers/patients can request blood.
* Hospitals can manage blood requirements.
* Blood banks can manage blood inventory.
* Administrators can manage the complete system.
* Users can search for available blood.
* Donation records can be maintained.
* Blood requests can be tracked.
* Notifications/status updates can be provided.
* Reports and dashboards can show useful statistics.

The application must be designed as a **real-world production-style system**, not just a basic CRUD project.

---

# 3. Core User Roles

The system should support role-based access.

## 3.1 Admin

Admin can:

* Manage users
* Manage donors
* Manage hospitals
* Manage blood banks
* Manage blood groups
* Manage donation records
* Manage blood requests
* Manage blood inventory
* Verify donor/hospital accounts
* View dashboards
* View reports
* Manage system settings

---

## 3.2 Donor

Donor can:

* Register
* Login
* Create/update profile
* Add blood group
* Add location
* View eligibility information
* View donation history
* View donation requests
* Accept/decline requests
* Track donation status
* View notifications

---

## 3.3 Blood Seeker / Patient

Blood seeker can:

* Register
* Login
* Create profile
* Search for blood
* Search donors/blood banks
* Create blood requests
* Track request status
* View request history
* Receive notifications

---

## 3.4 Hospital

Hospital can:

* Register
* Login
* Manage hospital profile
* Create blood requirements
* Search blood availability
* Manage blood requests
* Track requests
* View blood transactions
* Manage authorized staff

---

## 3.5 Blood Bank

Blood bank can:

* Manage profile
* Manage blood inventory
* Add blood units
* Remove expired units
* Update blood stock
* Manage blood requests
* Record blood collection
* Record blood issue/dispatch
* View inventory reports

---

# 4. Important Blood Groups

The system should support:

* A+
* A-
* B+
* B-
* AB+
* AB-
* O+
* O-

The architecture should allow additional configuration in the future rather than hard-coding unnecessary logic throughout the application.

---

# 5. Main Modules

The system should contain the following modules.

### Authentication

* Registration
* Login
* Logout
* JWT authentication
* Password management
* Role-based permissions

### User Management

* User profile
* Role
* Contact information
* Location
* Account status

### Donor Management

* Donor profile
* Blood group
* Eligibility information
* Availability
* Donation history

### Blood Request Management

* Create request
* Blood group
* Required units
* Urgency
* Hospital/patient information
* Location
* Request status

### Blood Inventory

* Blood group
* Units
* Collection date
* Expiry date
* Status
* Blood bank

### Blood Donation

* Donor
* Donation date
* Blood group
* Quantity
* Collection location
* Status

### Hospital Management

* Hospital registration
* Verification
* Hospital profile
* Blood requirements
* Requests

### Blood Bank Management

* Blood stock
* Donations
* Blood issue
* Expired units
* Inventory history

### Notifications

* Blood request notifications
* Donation notifications
* Status changes
* Account verification
* Important alerts

### Dashboard

Different dashboards for:

* Admin
* Donor
* Hospital
* Blood Bank
* Blood Seeker

### Reports

* Total donors
* Total donations
* Blood inventory
* Blood requests
* Completed requests
* Pending requests
* Blood group statistics
* Donation statistics

---

# 6. Suggested Architecture

Use a clean separation between frontend and backend.

```text
blood-donation-system/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── donors/
│   │   ├── hospitals/
│   │   ├── bloodbanks/
│   │   ├── donations/
│   │   ├── bloodrequests/
│   │   ├── inventory/
│   │   └── notifications/
│   │
│   └── ...
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── routes/
│   │   └── utils/
│   │
│   └── ...
│
├── docs/
│   ├── project-requirements.md
│   ├── api-documentation.md
│   ├── database-design.md
│   ├── setup-guide.md
│   └── development-progress.md
│
└── README.md
```

The exact structure may be changed if there is a strong technical reason. Explain the reason before making a major architectural change.

---

# 7. Development Phases

The project must be developed strictly in phases.

Do NOT attempt to build the entire system at once.

---

## PHASE 0 — Requirement Analysis & Planning

Before writing application code:

### Tasks

* Analyze the complete requirements.
* Identify functional requirements.
* Identify non-functional requirements.
* Identify user roles.
* Identify modules.
* Identify relationships between modules.
* Identify API requirements.
* Identify database entities.
* Identify authentication requirements.
* Identify frontend pages.
* Identify possible edge cases.

Create:

```text
docs/project-requirements.md
docs/database-design.md
docs/development-progress.md
```

### Deliverables

* Complete requirements
* Feature list
* User roles
* Initial database design
* Initial API plan
* Frontend page plan
* Development roadmap

### Git

After completing the phase:

```bash
git add .
git commit -m "docs: add project requirements and architecture"
git push origin <current-branch>
```

---

# PHASE 1 — Project Setup

### Backend

Set up:

* Python environment
* Django
* Django REST Framework
* MySQL connection
* Environment variables
* CORS
* Project configuration
* Base API structure

### Frontend

Set up:

* React
* Vite
* Routing
* Axios
* UI framework
* Environment variables
* Base folder structure

### Git

Test both applications.

Then:

```bash
git add .
git commit -m "chore: initialize frontend and backend"
git push origin <current-branch>
```

---

# PHASE 2 — Database & Backend Foundation

Create the core Django models.

Possible entities:

```text
User
Role
Donor
Hospital
BloodBank
BloodGroup
Donation
BloodRequest
BloodInventory
Notification
```

Tasks:

* Design relationships
* Create models
* Create migrations
* Apply migrations
* Add admin configuration
* Add model validation
* Create serializers
* Create basic API structure

Test all models and relationships.

Commit and push.

---

# PHASE 3 — Authentication & Authorization

Implement:

* Registration
* Login
* JWT authentication
* Refresh token
* Logout strategy
* Password hashing
* User roles
* Role-based permissions
* Protected APIs

Test:

* Valid login
* Invalid login
* Unauthorized API request
* Role restrictions
* Token expiration
* Protected routes

Commit and push.

---

# PHASE 4 — Donor Module

Implement:

* Donor registration/profile
* Blood group
* Location
* Contact information
* Availability
* Eligibility fields
* Donation history
* Donor dashboard

APIs must be properly validated.

Frontend must consume APIs through Axios.

Test complete donor workflow.

Commit and push.

---

# PHASE 5 — Blood Request Module

Implement:

* Create request
* Update request
* Cancel request
* Request status
* Blood group
* Required units
* Urgency
* Patient details
* Hospital information
* Location

Possible statuses:

```text
Pending
Approved
Matched
Processing
Completed
Cancelled
Rejected
```

Implement both backend and frontend.

Test the complete workflow.

Commit and push.

---

# PHASE 6 — Hospital Module

Implement:

* Hospital registration
* Hospital profile
* Verification
* Hospital dashboard
* Blood requests
* Request management
* Blood availability search
* Request tracking

Implement proper permissions.

Commit and push.

---

# PHASE 7 — Blood Bank Module

Implement:

* Blood bank registration
* Verification
* Inventory
* Blood units
* Collection records
* Issue/dispatch
* Expiry management
* Stock updates
* Inventory history

Implement transaction-safe inventory updates.

Example:

```text
Available Units
+
Blood Donation
-
Blood Issued
-
Expired Blood
=
Current Inventory
```

Commit and push.

---

# PHASE 8 — Blood Donation Module

Implement:

* Donation scheduling
* Donation record
* Donor
* Blood group
* Quantity
* Donation date
* Collection location
* Status

Possible status:

```text
Scheduled
Completed
Cancelled
Rejected
```

Update donor donation history automatically.

Commit and push.

---

# PHASE 9 — Blood Search & Matching

Create a search system.

Users should be able to search by:

* Blood group
* Location
* Availability
* Blood bank
* Hospital

Create appropriate matching logic.

The system should never expose unnecessary personal information.

Commit and push.

---

# PHASE 10 — Notification System

Implement notifications for events such as:

* New blood request
* Request accepted
* Request rejected
* Donation scheduled
* Donation completed
* Request status changed
* Account verification

Start with in-app notifications.

Email/SMS can be considered as a future extension.

Commit and push.

---

# PHASE 11 — Dashboards

Create dashboards for each role.

## Admin Dashboard

Show:

* Total users
* Total donors
* Total hospitals
* Total blood banks
* Total requests
* Completed requests
* Pending requests
* Blood inventory

## Donor Dashboard

Show:

* Profile
* Availability
* Donation history
* Active requests
* Notifications

## Hospital Dashboard

Show:

* Active requests
* Blood requirements
* Available blood
* Request history

## Blood Bank Dashboard

Show:

* Inventory
* Blood collections
* Blood issued
* Expired units
* Stock statistics

Commit and push.

---

# PHASE 12 — Admin Panel

Implement administrative controls:

* User management
* Donor verification
* Hospital verification
* Blood bank verification
* Request management
* Inventory monitoring
* Donation monitoring
* Notifications
* Reports

Admin actions must be protected by permissions.

Commit and push.

---

# PHASE 13 — Reports & Analytics

Create:

* Donation reports
* Blood inventory reports
* Blood request reports
* Blood group statistics
* Monthly donation statistics
* Request completion statistics

Use charts where useful.

Do not overload dashboards with unnecessary charts.

Commit and push.

---

# PHASE 14 — Frontend UI/UX Refinement

Improve:

* Responsive design
* Navigation
* Forms
* Tables
* Cards
* Modals
* Loading states
* Error states
* Empty states
* Toast messages
* Accessibility
* Mobile responsiveness

Maintain consistent design throughout the application.

Commit and push.

---

# PHASE 15 — Testing & Security

Backend:

* Model tests
* API tests
* Authentication tests
* Permission tests
* Validation tests
* Request workflow tests
* Inventory tests

Frontend:

* Component testing where appropriate
* Form validation
* API error handling
* Route protection

Security review:

* Authentication
* Authorization
* CORS
* CSRF where applicable
* Environment variables
* Sensitive data
* Input validation
* API permissions
* SQL injection protection
* XSS protection

Commit and push.

---

# PHASE 16 — Documentation

Complete:

```text
README.md
docs/project-requirements.md
docs/database-design.md
docs/api-documentation.md
docs/setup-guide.md
docs/development-progress.md
```

README should include:

* Project overview
* Features
* Tech stack
* Architecture
* Installation
* Environment variables
* Database setup
* Backend setup
* Frontend setup
* API overview
* User roles
* Running the project
* Testing
* Git workflow

Commit and push.

---

# PHASE 17 — Final Review & Deployment Preparation

Perform a complete project audit.

Check:

* Frontend works
* Backend works
* Database works
* Authentication works
* APIs work
* Role permissions work
* Forms work
* Blood requests work
* Donations work
* Inventory works
* Dashboards work
* Notifications work
* No obvious console errors
* No sensitive credentials committed
* Documentation is complete

Prepare deployment configuration.

Do NOT deploy automatically unless explicitly instructed.

Final commit:

```bash
git add .
git commit -m "chore: finalize blood donation management system"
git push origin <current-branch>
```

---

# 8. STRICT DEVELOPMENT RULES

These rules are mandatory.

## RULE 1 — Do Not Start Without Clarification

Before starting any phase, analyze the requirements.

If anything is unclear, ambiguous, conflicting, missing, or requires a design decision:

**STOP.**

Ask the user a question.

Do not make assumptions about important business logic.

---

# RULE 2 — Ask Before Starting Every Phase

After finishing a phase:

1. Explain what was completed.
2. Show the important changes.
3. Show testing results.
4. Show Git commit/push status.
5. Ask:

> "Phase X is complete. Shall I start Phase X+1?"

Do not automatically start the next phase.

---

# RULE 3 — Never Skip Phases

The development order must be:

```text
Phase 0
↓
Phase 1
↓
Phase 2
↓
Phase 3
↓
...
↓
Phase 17
```

Do not jump directly to frontend screens while backend architecture is incomplete unless the user explicitly approves the change.

---

# RULE 4 — One Phase at a Time

Only work on the currently approved phase.

Do not silently implement features belonging to future phases.

If implementation requires something from a future phase, explain the dependency first.

---

# RULE 5 — Git Commit Is Mandatory

Every completed phase must have a Git commit.

Use meaningful conventional commit messages.

Examples:

```bash
feat: add donor management module
feat: implement blood request workflow
fix: resolve inventory calculation issue
docs: update API documentation
test: add authentication API tests
refactor: improve donor service structure
```

---

# RULE 6 — Git Push Is Mandatory

After every successful phase commit:

```bash
git push origin <current-branch>
```

The AI must not consider a phase complete until the commit has been pushed successfully.

If push fails:

**STOP and report the error.**

Do not claim that the phase is complete.

---

# RULE 7 — STRICT NO CO-AUTHOR RULE

Every Git commit must be created **without any `Co-authored-by` trailer**.

Never add:

```text
Co-authored-by:
```

Never add AI attribution to Git commits.

Before finalizing commits, verify the commit message does not contain a `Co-authored-by` line.

---

# RULE 8 — Never Rewrite Git History

Do not use:

```bash
git reset --hard
git rebase
git push --force
git push --force-with-lease
```

unless the user explicitly requests it.

Protect the existing Git history.

---

# RULE 9 — Never Commit Secrets

Never commit:

```text
.env
API keys
database passwords
JWT secrets
private credentials
tokens
passwords
```

Use:

```text
.env
.env.example
```

The `.env.example` file should contain placeholders only.

---

# RULE 10 — Test Before Commit

Before committing a phase:

1. Run appropriate tests.
2. Check backend.
3. Check frontend.
4. Check for errors.
5. Fix issues.
6. Re-test.
7. Commit.
8. Push.

Never commit known broken functionality unless the user explicitly asks to preserve it.

---

# RULE 11 — Do Not Hide Errors

If something fails:

Do not pretend it works.

Clearly report:

```text
Problem
Cause
What was attempted
Current status
Next required action
```

---

# RULE 12 — Do Not Overengineer

Build only what is required.

Avoid adding unnecessary:

* Libraries
* Microservices
* Complex architecture
* AI features
* Payment systems
* External services

unless required by the project.

---

# RULE 13 — Reuse Existing Code Carefully

Before creating a new utility/component/service:

Check whether an existing implementation can be reused.

Avoid duplicate:

```text
components
API functions
validators
utilities
styles
models
```

---

# RULE 14 — Backend First for Business Logic

Important business rules should be enforced by Django/Django REST Framework.

Do not rely only on React validation for:

* Permissions
* Blood request rules
* Inventory updates
* Authentication
* Authorization
* Sensitive operations

Frontend validation improves UX but backend validation provides the actual protection.

---

# RULE 15 — API-First Communication

React should communicate with Django through REST APIs.

Do not directly connect React to MySQL.

Architecture:

```text
React
  ↓
REST API
  ↓
Django REST Framework
  ↓
Django Models
  ↓
MySQL
```

---

# RULE 16 — Maintain Documentation During Development

Do not wait until the end to write documentation.

Update documentation whenever there is a major:

* API change
* Database change
* Architecture change
* Authentication change
* Feature addition
* Configuration change

---

# RULE 17 — Keep Development Progress Updated

Maintain:

```text
docs/development-progress.md
```

For every phase record:

```text
Phase:
Status:
Date:
Completed:
Files changed:
Tests:
Git commit:
Git push:
Issues:
```

---

# RULE 18 — Ask Before Major Architecture Changes

If you discover a better architecture during development, do not silently replace the existing architecture.

Explain:

```text
Current approach
Proposed approach
Reason
Advantages
Potential impact
```

Then ask for approval.

---

# RULE 19 — No Fake Data in Production Logic

Mock data can be used during UI development when necessary.

Clearly mark it as mock data.

Do not accidentally leave mock data connected to production functionality.

---

# RULE 20 — Maintain Clean Code

Follow:

* PEP 8 for Python
* Meaningful variable names
* Small reusable functions
* Proper React component structure
* Proper API service separation
* Clear error handling
* Comments only where useful

---

# 9. Required AI Agent Workflow

For every phase, follow this exact workflow.

```text
1. Read current project state
        ↓
2. Read documentation
        ↓
3. Check Git status
        ↓
4. Analyze the approved phase
        ↓
5. Identify ambiguity
        ↓
6. Ask questions if necessary
        ↓
7. Wait for clarification
        ↓
8. Implement only approved phase
        ↓
9. Test
        ↓
10. Fix issues
        ↓
11. Update documentation
        ↓
12. Check Git diff
        ↓
13. Create commit
        ↓
14. Verify NO Co-authored-by
        ↓
15. Push to GitHub
        ↓
16. Verify push
        ↓
17. Report phase completion
        ↓
18. Ask permission for next phase
```

---

# 10. Initial Instruction to the AI Agent

When this project is first opened, the AI agent must NOT immediately start coding.

The first response should:

1. Read the repository.
2. Inspect existing files.
3. Check Git status.
4. Identify existing technologies.
5. Compare the current repository against this documentation.
6. Identify missing information.
7. Ask questions if necessary.

Then ask:

> "I have analyzed the project requirements and current repository. Phase 0 is ready to begin. Shall I start Phase 0 — Requirement Analysis & Planning?"

Do not write implementation code until the user approves Phase 0.

---

# 11. Phase Completion Response Format

After each phase, respond using:

```text
PHASE X — COMPLETED

Completed:
- ...
- ...
- ...

Files Changed:
- ...
- ...

Testing:
- ...
- ...

Git Commit:
<commit hash>

Git Push:
Successful

Co-authored-by:
None

Current Status:
Phase X completed successfully.

Next:
Shall I start Phase X+1?
```

If the phase failed:

```text
PHASE X — BLOCKED

Problem:
...

Cause:
...

Attempted:
...

Current Status:
Blocked

Required Action:
...
```

Do not report the phase as completed.

---

# 12. Definition of Done

A phase is considered complete only when:

* Required implementation is complete.
* Code is tested.
* No known blocking error exists.
* Documentation is updated.
* Git changes are reviewed.
* Commit is created.
* Commit contains no `Co-authored-by`.
* Commit is pushed successfully.
* User is informed.
* User is asked for approval before the next phase.

---

# 13. Final Project Definition

The final application should provide a complete workflow:

```text
User Registration
       ↓
Authentication
       ↓
Role-Based Dashboard
       ↓
Donor / Hospital / Blood Bank / Seeker
       ↓
Blood Search
       ↓
Blood Request
       ↓
Matching / Availability
       ↓
Donation / Blood Bank Processing
       ↓
Inventory Update
       ↓
Request Fulfillment
       ↓
Notification
       ↓
History & Reports
```

The system should be modular, secure, maintainable, responsive, documented, and suitable for future expansion.

---

# 14. MASTER COMMAND

The following instruction should be treated as the highest-level development instruction for the AI coding agent:

> Build the Blood Donation Management System using React.js for the frontend and Python Django + Django REST Framework for the backend, with MySQL as the database.
>
> Follow the project documentation and development phases strictly.
>
> Do not start implementation immediately. First inspect the existing repository, understand the current state, review Git status, and identify any ambiguity or missing requirements.
>
> If there is any confusion about requirements, architecture, business logic, database relationships, UI behavior, permissions, or implementation decisions that could materially affect the project, STOP and ask me before proceeding.
>
> Work on exactly one approved phase at a time.
>
> Never automatically start the next phase. After completing a phase, report the implementation, testing, documentation updates, Git commit, and Git push status, then ask for my approval to start the next phase.
>
> Before every commit, test the relevant functionality and review the Git diff.
>
> Every completed phase MUST be committed and pushed to GitHub.
>
> Every Git commit MUST NOT contain a `Co-authored-by` trailer or any AI attribution.
>
> Never commit secrets, passwords, API keys, tokens, or `.env` files.
>
> Never use force push or rewrite Git history unless I explicitly instruct you to do so.
>
> Never claim something works if it has not been tested.
>
> Never hide errors. Clearly report problems, causes, attempted solutions, and current status.
>
> Keep the documentation updated throughout development.
>
> Do not overengineer the project or introduce unnecessary dependencies.
>
> Backend business rules must be enforced on the server. React-side validation is for user experience and must not be treated as the security boundary.
>
> Follow clean-code practices and maintain a clear separation between frontend, backend, database, API services, and documentation.
>
> The project must be developed incrementally from Phase 0 through the final phase.
>
> **First action: inspect the repository and Git status. Do not modify application code. If clarification is needed, ask questions. Otherwise, explain the Phase 0 plan and ask for explicit approval to start Phase 0.**


MYSQL detail 

database : blood_db
user : root 
password : 