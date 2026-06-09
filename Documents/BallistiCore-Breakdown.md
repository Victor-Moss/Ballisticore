# BallistiCore — Project Breakdown

> Living document. Updated as the project progresses.
> Last updated: 2026-03-30 (Phase 12 expansion plan added)

---

## Project Overview

**System:** BallistiCore Firearms Register Management System
**Purpose:** Web-based replacement for the Excel/VBA firearms register. Tracks security guard firearm issuances, prevents double-booking, generates permits, delivers via print + WhatsApp, and maintains full SAPS-compliant audit trails.
**Deployment:** Internal network (LAN), browser-based, no internet exposure except outbound WhatsApp.

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python + FastAPI | Python 3.14.3 / FastAPI 0.115.12 |
| Database | PostgreSQL | 17.x |
| ORM | SQLAlchemy | 2.0.48 |
| Migrations | Alembic | 1.15.2 |
| DB Driver | psycopg (v3) | 3.2.13 |
| Auth | JWT via python-jose | 3.5.0 |
| Password Hashing | passlib + bcrypt | 1.7.4 / 5.0.0 |
| PDF Generation | WeasyPrint | 65.1 |
| WhatsApp | Twilio API | 9.6.2 |
| Excel Export | openpyxl | 3.1.5 |
| Frontend | React + Vite | React 19 / Vite 6 |
| CSS | Tailwind CSS | v3 |
| HTTP Client | Axios | latest |
| Routing | React Router | latest |

> **Note:** psycopg v3 (not psycopg2) — Python 3.14 has no pre-built wheels for psycopg2-binary.
> DB connection string uses `postgresql+psycopg://` prefix accordingly.

---

## Folder Structure

```
C:\sites\BallistiCore\
│
├── BallistiCore.code-workspace     ← Open this in VS Code
│
├── BallistiCore_app\
│   ├── backend\
│   │   ├── .venv\                  ← Python venv (backend only, DO NOT use root .venv)
│   │   ├── alembic\                ← DB migration scripts
│   │   │   └── versions\           ← Migration files go here
│   │   ├── app\
│   │   │   ├── main.py             ← FastAPI app entry point, CORS config
│   │   │   ├── core\
│   │   │   │   ├── config.py       ← Settings loaded from .env (pydantic-settings)
│   │   │   │   └── database.py     ← SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   │   ├── models\             ← SQLAlchemy ORM models (Phase 2)
│   │   │   ├── schemas\            ← Pydantic request/response schemas (Phase 3)
│   │   │   ├── routers\            ← FastAPI route handlers (Phase 3+)
│   │   │   ├── services\           ← Business logic (Phase 3+)
│   │   │   └── templates\          ← HTML templates for permit PDFs (Phase 5)
│   │   ├── permits\                ← Generated PDF permit files (gitignored)
│   │   ├── .env                    ← Secrets and config — never commit this
│   │   ├── .gitignore
│   │   ├── alembic.ini
│   │   └── requirements.txt
│   │
│   └── frontend\
│       ├── src\
│       │   ├── main.jsx            ← React entry point
│       │   ├── App.jsx             ← Root component (to be replaced Phase 8)
│       │   ├── index.css           ← Tailwind directives (@tailwind base/components/utilities)
│       │   ├── pages\              ← One file per screen (Phase 8)
│       │   ├── components\         ← Shared UI components (Phase 8)
│       │   ├── api\                ← Axios API call functions (Phase 8)
│       │   └── context\            ← AuthContext, JWT state (Phase 7)
│       ├── dist\                   ← Production build output (npm run build)
│       ├── tailwind.config.js      ← Content paths configured
│       ├── postcss.config.js
│       ├── vite.config.js
│       └── package.json
│
├── Documents\
│   ├── BallistiCore-Breakdown.md           ← THIS FILE
│   ├── BallistiCore_Implementation_Plan.md ← Full 11-phase build plan
│   ├── BallistiCore_Expansion_Plan.md      ← Phase 12 expansion plan (user perms, guard competency, etc.)
│   └── BallistiCore_Specifications.md      ← Functional specifications
│
├── Excel_Sample\
│   └── Firearms Permit.xlsm        ← REFERENCE ONLY — never modify
│
├── Bot_Brain\
│   └── Intro.md                    ← Workspace context for AI agents
│
├── Product_Owner\
│   └── Audio_Files\                ← Voice notes + transcripts from Victor
│
└── Scratch_Pad\                    ← Temp scripts, experiments, dumps only
    (analyze_excel.py, transcribe_audio.py live at root for now)
```

---

## Database

**Name:** `ballisticore_db`
**User:** `ballisticore_user`
**Password:** set in `.env` — default `ballisticore_pass` (change before production)
**Host:** localhost:5432
**Connection string:** `postgresql+psycopg://ballisticore_user:ballisticore_pass@localhost:5432/ballisticore_db`

### Setup SQL (run once after PostgreSQL install)
```sql
CREATE DATABASE ballisticore_db;
CREATE USER ballisticore_user WITH PASSWORD 'ballisticore_pass';
GRANT ALL PRIVILEGES ON DATABASE ballisticore_db TO ballisticore_user;
```

### Tables (Phase 2 — not yet created)

| Table | Purpose |
|-------|---------|
| `users` | Superadmin accounts (login, manage system) |
| `locations` | Sites/branches guards can be assigned to |
| `guards` | Security personnel — soft delete on departure |
| `firearms` | Firearm inventory (serial, make, calibre, license) |
| `guard_firearm_permissions` | Permission matrix — which guard can carry which firearm |
| `register` | Current active issuances (firearm_id is unique — enforces no double-booking) |
| `register_history` | Immutable audit trail of all issue/return events |
| `permits` | Issued permit records with PDF path and WhatsApp send status |

### Key Constraints
- `register.firearm_id` — UNIQUE constraint prevents double-booking at DB level
- `guard_firearm_permissions` — UNIQUE on (guard_id, firearm_id)
- Guards are NEVER hard deleted — `is_active = false` for departed staff
- `register_history` is append-only, never updated or deleted

---

## Environment Config (`.env`)

File location: `BallistiCore_app/backend/.env`

```
DATABASE_URL=postgresql+psycopg://ballisticore_user:ballisticore_pass@localhost:5432/ballisticore_db
SECRET_KEY=change-this-to-a-long-random-string-before-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
TWILIO_ACCOUNT_SID=          ← Fill in Phase 7
TWILIO_AUTH_TOKEN=           ← Fill in Phase 7
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
PDF_STORAGE_PATH=permits/
ENVIRONMENT=development
```

---

## Key Commands

### Backend
```bash
# Working directory: BallistiCore_app/backend

# Activate venv (Windows)
.venv\Scripts\activate

# Run dev server (with auto-reload)
uvicorn app.main:app --reload

# API docs (when server is running)
http://localhost:8000/docs

# Run migrations
alembic upgrade head

# Generate new migration after model changes
alembic revision --autogenerate -m "description"

# Roll back one migration
alembic downgrade -1
```

### Frontend
```bash
# Working directory: BallistiCore_app/frontend

# Dev server (hot reload)
npm run dev
# Runs at: http://localhost:5173

# Production build
npm run build
```

---

## Build Progress

### Phase 1 — Environment & Scaffold ✅ COMPLETE
- [x] Backend folder structure created
- [x] Python venv created (Python 3.14.3)
- [x] All packages installed (FastAPI, SQLAlchemy, Alembic, psycopg3, WeasyPrint, Twilio, etc.)
- [x] `main.py` with health check route
- [x] `core/config.py` — settings from .env
- [x] `core/database.py` — SQLAlchemy engine + get_db()
- [x] `.env` template created
- [x] Alembic initialised and wired to models + .env
- [x] React + Vite frontend scaffolded
- [x] Tailwind CSS installed and configured
- [x] Axios + React Router installed
- [x] Frontend builds cleanly (`npm run build` ✅)
- [x] `app loaded ok` confirmed ✅
- [x] PostgreSQL 17.9 installed, `ballisticore_db` created ✅

---

### Phase 2 — Database Schema ✅ COMPLETE
- [x] SQLAlchemy models for all 8 tables (`users`, `locations`, `guards`, `firearms`, `guard_firearm_permissions`, `register`, `register_history`, `permits`)
- [x] Alembic initial migration generated (`084d3051bff7_initial_schema.py`)
- [x] Migration applied (`alembic upgrade head` ✅)
- [x] All 8 tables verified in PostgreSQL ✅

---

### Phase 3 — Backend API: Core CRUD ✅ COMPLETE
- [x] Pydantic schemas — `location`, `guard`, `firearm`, `permission`
- [x] Services — `locations`, `guards`, `firearms`, `permissions` (all DB logic)
- [x] Routers — `GET/POST/PUT/DELETE` for all 4 resources
- [x] Guards: duplicate ID number check (409), soft deactivate/reactivate endpoints
- [x] Firearms: `is_available` flag computed per firearm on every response
- [x] Permissions: upsert logic (set once, update if exists)
- [x] All routers registered in `main.py`
- [x] Live tested: health ✅ guards ✅ firearms ✅ locations POST + GET ✅
- [x] API docs available at `http://localhost:8000/docs`

### Phase 4 — Issuance Engine ✅ COMPLETE
- [x] `schemas/register.py` — IssueRequest, ReturnRequest, RegisterEntryOut, HistoryEntryOut
- [x] `services/issuance.py` — full validation chain: guard active → firearm active → permission check → availability check
- [x] `services/users.py` — password hashing, user lookup, seed_admin
- [x] `routers/register.py` — issue, return, current register, history (filterable)
- [x] Admin user auto-seeded on startup via lifespan event
- [x] Live tested:
  - Issue firearm ✅ — permit_id generated (BC-YYYYMMDD-NNNN format)
  - Double-book blocked ✅ — 409 "Firearm GL-9MM-001 is currently issued to John Smith"
  - Unauthorized guard blocked ✅ — 403 "No Permission is not authorised to carry firearm GL-9MM-001"
  - Current register shows live issuance ✅
  - Return firearm ✅ — register cleared
  - History shows ISSUED + RETURNED entries ✅
Core double-booking prevention + issue/return logic

### Phase 5 — Permit PDF Generation ✅ COMPLETE
- [x] `services/permit_generator.py` — ReportLab-based (not WeasyPrint — see note 11)
- [x] Full permit PDF — A4, guard details, firearm details, period, authorisation, return section
- [x] Mini permit PDF — 85×140mm card, all key fields, compact layout
- [x] `routers/permits.py` — list, get, generate, download full, download mini
- [x] PDF auto-generated on every firearm issuance (non-blocking — failure doesn't break issuance)
- [x] Permit number format: `BC-YYYYMMDD-NNNN`
- [x] PDFs stored in `backend/permits/` (gitignored)
- [x] `has_pdf` flag on permit response — true when file exists on disk
- [x] Live tested: `BC-20260329-0002_full.pdf` + `BC-20260329-0002_mini.pdf` generated ✅
Full permit + mini permit HTML templates → WeasyPrint → PDF

### Phase 6 — Authentication ✅ COMPLETE
- [x] `core/auth.py` — JWT creation, token decode, `get_current_user` dependency, `require_active_user`
- [x] `schemas/user.py` — UserCreate, UserOut, TokenOut
- [x] `routers/auth.py` — POST `/login`, GET `/me`, POST `/users`, GET `/users`, PUT `/users/{id}/deactivate`
- [x] All API routers protected via `dependencies=[Depends(require_active_user)]` at router level
- [x] `/health` remains public
- [x] Login uses OAuth2PasswordRequestForm (form-data — compatible with `/docs` Authorize button)
- [x] Live tested:
  - Unauthenticated request → 401 ✅
  - Wrong password → 401 ✅
  - Valid login → token + user returned ✅
  - `/me` with token → username + active status ✅
  - Protected route with token → data returned ✅
  - Protected route with bad token → 401 ✅

### Phase 7 — WhatsApp Integration ✅ COMPLETE
- [x] `services/whatsapp.py` — `send_permit_whatsapp()` and `send_permit_whatsapp_with_pdf()`
- [x] SA number normalisation — `0821234567` → `+27821234567` → `whatsapp:+27821234567`
- [x] Graceful no-op when Twilio credentials not set (logs warning, doesn't crash)
- [x] Auto-triggered as `BackgroundTask` on every firearm issuance (guard must have `cell_phone`)
- [x] `POST /api/permits/{id}/resend-whatsapp` — manual retry with optional number override
- [x] `permit.whatsapp_sent` + `whatsapp_sent_at` updated on successful send
- [x] Live tested: issue → WhatsApp queued → `whatsapp_sent: False` (no creds) ✅ | resend endpoint returns queued message ✅

**To activate WhatsApp:**
1. Sign up at twilio.com
2. Enable WhatsApp sandbox (or buy a number)
3. Add `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` to `backend/.env`
4. Change `TWILIO_WHATSAPP_FROM` to your Twilio WhatsApp number
5. Restart the server — sends will fire automatically on next issuance

### Phase 8 — Frontend (React Screens) ✅ COMPLETE
- [x] `src/context/AuthContext.jsx` — JWT token + user state, login/logout
- [x] `src/components/Layout.jsx` — dark sidebar nav + main content wrapper
- [x] Login, Dashboard, Guards list, Guard detail/edit + permissions
- [x] Firearms list + add/edit
- [x] Issue Firearm, Return Firearm
- [x] Current Register (with PDF download links)
- [x] Register History (with guard/firearm/date filters)
- [x] Permits list (PDF downloads + WhatsApp resend)
- [x] Admin — user management (admin-only)
- [x] React Router with protected + public route guards
- [x] `issued_by` / `actioned_by` taken from logged-in user on issue/return

### Phase 9 — Reporting & SAPS Exports ✅ COMPLETE
- [x] `services/reports.py` — openpyxl Excel generation (styled workbooks)
- [x] `routers/reports.py` — 3 endpoints, all return binary xlsx
- [x] `GET /api/reports/register` — current register snapshot export
- [x] `GET /api/reports/history` — date/guard/firearm filtered audit export
- [x] `GET /api/reports/guard/{id}` — single guard activity report
- [x] Frontend `src/api/reports.js` — blob download helper (uses Bearer token, triggers browser save)
- [x] Export Excel button on Register page
- [x] Export Excel + Guard Report buttons on History page
- [x] Alembic migration: added `guards.psira_number`, made `id_number` nullable

### Phase 10 — Testing & QA ✅ COMPLETE
- [x] pytest + pytest-asyncio + httpx installed (added to requirements.txt)
- [x] `tests/conftest.py` — in-memory SQLite with StaticPool (isolated from PostgreSQL), seed helpers: `make_user`, `make_guard`, `make_firearm`, `make_permission`, `auth_headers`
- [x] `tests/test_auth.py` — JWT creation, login endpoint (valid/wrong/unknown), protected routes, public /health
- [x] `tests/test_guards_api.py` — list (active/inactive/filter), create, deactivate, reactivate
- [x] `tests/test_issuance.py` — permit number format, full 7-step validation chain, double-booking (4 scenarios), return flow (4 scenarios)
- [x] `tests/test_register_api.py` — HTTP-layer integration tests for issue, return, history (filter by guard), full flow
- [x] **48 / 48 tests passing** ✅
- [x] Schema fixes discovered during testing: `is_admin` added to User model, `email` made nullable, `psira_number` confirmed on Guard model
- [x] Migration applied: `4295c76d2d5c_add_is_admin_to_users_make_email_.py`

**To run tests:**
```bash
cd BallistiCore_app/backend
.venv\Scripts\activate
pytest
```

### Phase 11 — LAN Deployment ✅ COMPLETE
- [x] `CORS_ORIGINS` moved to `.env` — configurable per environment without code changes
- [x] React frontend production build confirmed (`npm run build` → `dist/` ✅)
- [x] `deploy/nginx.conf` — Nginx config: serves React `dist/`, proxies `/api/` and `/health` to FastAPI :8000 on loopback, 1-year cache on static assets, 20MB body limit for PDF/Excel downloads
- [x] `deploy/start_backend.bat` — uvicorn startup script for NSSM (4 workers, loopback-only)
- [x] `deploy/backup_db.bat` — daily `pg_dump` backup to `C:\sites\BallistiCore\backups\`, auto-purge after 30 days
- [x] `deploy/restore_db.bat` — guided restore from `.dump` file with confirmation prompt
- [x] `deploy/env.production.template` — production `.env` checklist (SECRET_KEY, CORS_ORIGINS, PDF_STORAGE_PATH)
- [x] `deploy/DEPLOYMENT.md` — complete 10-step deployment guide: LAN IP, Nginx, NSSM service, firewall, Task Scheduler backup, verify checklist, security checklist, update procedures, troubleshooting table
- [x] `backups/` and `permits/` folders created on disk
- [x] 48/48 tests still passing after CORS change ✅

**To deploy on the production server:**
```
1. Copy entire C:\sites\BallistiCore\ to the server
2. Follow deploy\DEPLOYMENT.md step by step
3. Change admin password on first login
```

### Phase 12 — Expansion (User Permissions + Guard Competency + Permit/Register Fields) ✅ COMPLETE
Full plan: `Documents/BallistiCore_Expansion_Plan.md`

> Verified 2026-06-03: all of 12a–12e are implemented end-to-end (migrations
> `4014436835fd`, `1210dc2fbd2d`, `afcaf906e07c`, `995cc4b956f9`,
> `c2fb0d8f1704`; models, schemas, services and frontend pages all carry the
> new fields). The boxes below were never ticked, but the work is done.

**12a — User management expansion**
- [ ] 5 extra profile fields: `personnel_number`, `psira_number`, `competency`, `phone_number`, `id_number`
- [ ] 12 granular permission booleans (new_permits, return_permits, manage_weapons, manage_staff, access_database, send_whatsapp, view_register_history, system_admin, add_user, modify_user, change_passwords, clear_logs)
- [ ] 4 weapon-category permissions: `perm_carbine`, `perm_handgun`, `perm_rifle`, `perm_shotgun`
- [ ] Alembic migration with `server_default='false'` on all new booleans
- [ ] Expanded Admin page (Add/Edit User modal matching Excel dialog layout)
- [ ] Page-level permission gating in frontend (check granular perms, not just `is_admin`)

**12b — Guard model expansion**
- [ ] 2 extra profile fields: `region`, `personnel_number`
- [ ] 8 SAPS competency fields: `saps_comp_{carbine,handgun,rifle,shotgun}` + `saps_expiry_{...}`
- [ ] 4 weapon-type clearance flags: `permitted_carbine/handgun/rifle/shotgun`
- [ ] New table: `guard_cit_routes` (guard_id, route_name, cell_phone)
- [ ] Expanded GuardDetail page: SAPS competency section + CIT routes section

**12c — Firearm type field**
- [ ] `firearm_type` column on `firearms` table (carbine / handgun / rifle / shotgun)
- [ ] Dropdown in FirearmDetail edit form
- [ ] Issuance validation: check guard's weapon-type clearance matches firearm type

**12d — Permit model expansion**
- [ ] `rounds_issued`, `rounds_returned`
- [ ] `period_from_time`, `valid_until_time`
- [ ] `posted`, `cit_cell_route`, `witness`, `remarks`
- [ ] `firearm_returned_correct`, `in_order`
- [ ] `saps_competency_number` (snapshot at time of issue)
- [ ] Updated Issue + Return pages + PDF permit layout

**12e — Register model expansion**
- [ ] `ammunition_issued`, `ammunition_returned`
- [ ] `firearm_inspected_correct`, `firearm_returned_correct`, `permit_returned`
- [ ] `guard_signature`, `authorising_officer_signature`, `audit_signature`
- [ ] `cit_id`, `responsible_person_name`
- [ ] Updated Register + History pages showing new columns

### Phase 13 — Guard Electronic Signature + Self-Service Accounts ✅ COMPLETE (2026-06-03)
Guards now have their own sign-in identity, kept **separate** from operator `users`
(a guard login can only sign for a firearm — it carries no system access).

- [x] Migration `e7efa56627a9` — guard account columns (`username`, `hashed_password`,
      `must_change_password`, `password_set_at`, `last_signin_at`, OTP reset fields)
      + `guard_signed`/`guard_signed_at` on `permits`, `register`, `register_history`
      (+ `guard_signature_method` on permits). All new booleans use `server_default='false'`.
- [x] `services/guard_auth.py` — account create/reset, password verify, OTP generate/verify
      (10-min TTL, 5-attempt lockout), username recovery
- [x] WhatsApp helpers `send_guard_otp` / `send_guard_username` (reuse Twilio)
- [x] **Signing at the operator terminal:** `POST /api/register/issue` takes `guard_password`.
      A guard *with* an account MUST enter a correct password to be issued (400 if missing,
      403 if wrong). A guard *without* an account is issued **unsigned** (rollout-friendly).
      Signature is stamped on permit/register/history and printed on the permit PDF.
- [x] Operator endpoints (gated by `require_change_passwords` = admin or `perm_change_passwords`):
      `POST /api/guards/{id}/account`, `PUT /api/guards/{id}/account/reset-password`,
      `DELETE /api/guards/{id}/account`
- [x] Public self-service router `/api/guard-account/*` — `forgot-username`, `request-reset`,
      `reset-password` (generic responses to prevent account enumeration)
- [x] Frontend: IssueFirearm signing step + inline "forgot password → OTP" flow;
      GuardDetail "Sign-in Account" card (create / reset / remove); Permits "Signed" column
- [x] Tests: `tests/test_guard_auth.py` (18 tests). Full suite **66/66 passing**.

> **Production note (WhatsApp OTP):** dev uses the Twilio WhatsApp *sandbox*, which
> requires each number to "join" and only allows free-form sends inside a 24h window.
> For production OTP, switch to **Twilio Verify** (or an approved WhatsApp template) —
> see `services/whatsapp.py`. The operator password-reset fallback works with no internet.

---

## Known Notes & Decisions

| # | Note |
|---|------|
| 1 | Root `.venv` (at `C:\sites\BallistiCore\`) is for `transcribe_audio.py` / `analyze_excel.py` — whisper/torch packages. Do not use for backend. |
| 2 | Backend uses its own `.venv` at `BallistiCore_app/backend/.venv` |
| 3 | psycopg v3 used instead of psycopg2 — Python 3.14 has no pre-built psycopg2-binary wheels |
| 4 | DB connection string prefix is `postgresql+psycopg://` (not `postgresql://`) |
| 5 | `Excel_Sample/Firearms Permit.xlsm` is sacred — reference only, never modify |
| 6 | `Scratch_Pad/` is the only place for temp scripts, experiments, and dumps |
| 7 | PostgreSQL 17.9 installed 2026-03-29, port 5432. postgres superuser password reset to 'postgres'. |
| 8 | SQLAlchemy 2.0.40 has Python 3.14 bug with Optional types — upgraded to 2.0.48 which fixes it. |
| 9 | PostgreSQL 15+ removed default CREATE on public schema — must run `GRANT ALL ON SCHEMA public TO ballisticore_user` after DB creation. |
| 10 | bcrypt 5.0.0 broke passlib 1.7.4 — pinned to `bcrypt==4.0.1` in requirements.txt. |
| 11 | WeasyPrint requires GTK/Pango system libraries (not available on Windows without MSYS2). Switched to ReportLab which is pure Python. WeasyPrint removed from requirements. |
