# BallistiCore — Implementation Plan

**System:** Firearms Register Management System
**Stack:** Python + FastAPI | PostgreSQL | React + Vite + Tailwind CSS | Twilio | WeasyPrint
**Location:** `C:\sites\BallistiCore\`

---

## Folder Structure

```
C:\sites\BallistiCore\
├── BallistiCore_app/
│   ├── backend/          ← FastAPI app
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/   ← SQLAlchemy models
│   │   │   ├── schemas/  ← Pydantic schemas
│   │   │   ├── routers/  ← API route files
│   │   │   ├── services/ ← Business logic
│   │   │   └── core/     ← Config, auth, DB session
│   │   ├── alembic/      ← DB migrations
│   │   ├── .env
│   │   └── requirements.txt
│   └── frontend/         ← React + Vite app
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   ├── api/
│       │   └── main.jsx
│       └── package.json
├── Documents/
├── Excel_Sample/         ← Reference only, never modify
├── Bot_Brain/
├── Product_Owner/
└── Scratch_Pad/          ← Temp scripts, experiments only
```

---

## Phase 1 — Environment & Project Scaffold

**Goal:** Working skeleton — backend returns a response, frontend loads in browser, DB is reachable.

### Tasks
- [ ] Create `BallistiCore_app/backend/` folder
- [ ] Create and activate Python virtual environment: `python -m venv .venv`
- [ ] Install backend packages:
  ```
  fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv
  passlib[bcrypt] python-jose[cryptography] weasyprint reportlab
  twilio openpyxl
  ```
- [ ] Create `backend/.env`:
  ```
  DATABASE_URL=postgresql://ballisticore_user:yourpassword@localhost:5432/ballisticore_db
  SECRET_KEY=your-secret-key-here
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=480
  TWILIO_ACCOUNT_SID=
  TWILIO_AUTH_TOKEN=
  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
  ```
- [ ] Create `backend/app/main.py` with FastAPI app and health check route
- [ ] Initialise Alembic: `alembic init alembic`
- [ ] Create PostgreSQL database and user:
  ```sql
  CREATE DATABASE ballisticore_db;
  CREATE USER ballisticore_user WITH PASSWORD 'yourpassword';
  GRANT ALL PRIVILEGES ON DATABASE ballisticore_db TO ballisticore_user;
  ```
- [ ] Create `BallistiCore_app/frontend/` with Vite + React:
  ```
  npm create vite@latest frontend -- --template react
  cd frontend && npm install
  npm install -D tailwindcss postcss autoprefixer
  npm install axios react-router-dom
  ```
- [ ] Initialise Tailwind in frontend
- [ ] Confirm: `uvicorn app.main:app --reload` runs; `npm run dev` loads in browser

---

## Phase 2 — Database Schema

**Goal:** All tables created via Alembic migration, ready for data.

### Tables

#### `users` — Superadmin accounts
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| username | VARCHAR(50) | unique |
| email | VARCHAR(100) | unique |
| hashed_password | TEXT | bcrypt |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMP | |

#### `locations` — Sites/branches
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(100) | |
| address | TEXT | |
| is_active | BOOLEAN | |

#### `guards` — Security personnel
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| first_name | VARCHAR(50) | |
| last_name | VARCHAR(50) | |
| id_number | VARCHAR(20) | unique |
| cell_phone | VARCHAR(20) | |
| email | VARCHAR(100) | |
| physical_address | TEXT | |
| location_id | UUID FK → locations | nullable |
| is_active | BOOLEAN | soft delete — never hard delete |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `firearms` — Firearm inventory
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| serial_number | VARCHAR(50) | unique |
| make | VARCHAR(50) | e.g. Glock, Beretta |
| model | VARCHAR(50) | |
| type | VARCHAR(30) | e.g. Pistol, Revolver |
| calibre | VARCHAR(20) | e.g. 9mm, .38 |
| license_number | VARCHAR(50) | |
| license_issue_date | DATE | |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |

#### `guard_firearm_permissions` — Who can carry what
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| guard_id | UUID FK → guards | |
| firearm_id | UUID FK → firearms | |
| is_permitted | BOOLEAN | true = allowed, false = explicitly blocked |
| created_at | TIMESTAMP | |
| UNIQUE | (guard_id, firearm_id) | |

#### `register` — Current active issuances
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| guard_id | UUID FK → guards | |
| firearm_id | UUID FK → firearms | unique — enforces no double-booking |
| issued_by | UUID FK → users | |
| issued_at | TIMESTAMP | |
| permit_id | UUID FK → permits | nullable |

#### `register_history` — Immutable audit trail
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| guard_id | UUID FK → guards | |
| firearm_id | UUID FK → firearms | |
| action | VARCHAR(20) | 'ISSUED' or 'RETURNED' |
| actioned_by | UUID FK → users | |
| actioned_at | TIMESTAMP | |
| notes | TEXT | nullable |

#### `permits` — Issued permit records
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| permit_number | VARCHAR(30) | auto-generated, unique |
| guard_id | UUID FK → guards | |
| firearm_id | UUID FK → firearms | |
| issued_by | UUID FK → users | |
| issued_at | TIMESTAMP | |
| valid_date | DATE | |
| whatsapp_sent | BOOLEAN | default false |
| whatsapp_sent_at | TIMESTAMP | nullable |
| pdf_path | TEXT | path to stored PDF |

### Tasks
- [ ] Write SQLAlchemy models for all tables in `backend/app/models/`
- [ ] Configure `alembic/env.py` to point at models
- [ ] Generate initial migration: `alembic revision --autogenerate -m "initial schema"`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify all tables exist in PostgreSQL

---

## Phase 3 — Backend API: Core Data (CRUD)

**Goal:** Full CRUD endpoints for guards, firearms, permissions, locations.

### Routers to build

#### `/api/guards`
- `GET /` — list all guards (with active filter)
- `GET /{id}` — get single guard + their permissions
- `POST /` — create guard
- `PUT /{id}` — update guard
- `PUT /{id}/deactivate` — soft delete (set is_active = false)
- `PUT /{id}/reactivate` — reinstate guard

#### `/api/firearms`
- `GET /` — list all firearms (with status: available/issued)
- `GET /{id}` — single firearm
- `POST /` — add firearm
- `PUT /{id}` — update firearm

#### `/api/permissions`
- `GET /guard/{guard_id}` — all permissions for a guard
- `POST /` — set permission (guard_id, firearm_id, is_permitted)
- `DELETE /{id}` — remove permission entry

#### `/api/locations`
- Full CRUD

### Tasks
- [ ] Create Pydantic schemas (request/response) in `backend/app/schemas/`
- [ ] Create SQLAlchemy CRUD helpers in `backend/app/services/`
- [ ] Build all routers in `backend/app/routers/`
- [ ] Register routers in `main.py`
- [ ] Test all endpoints via FastAPI docs at `http://localhost:8000/docs`

---

## Phase 4 — Firearm Issuance Engine

**Goal:** Core business logic — the system prevents double-booking and unauthorized issuances.

### Issuance Logic (in `backend/app/services/issuance.py`)

```
ISSUE FIREARM:
1. Check guard exists and is active
2. Check firearm exists and is active
3. Check guard_firearm_permissions — is_permitted must be true
   → If no permission record OR is_permitted = false: BLOCK, return error
4. Check register — is firearm already issued?
   → If firearm_id exists in register: BLOCK, return "Firearm currently with [Guard Name]"
5. All checks pass:
   → Insert into register
   → Insert into register_history (action='ISSUED')
   → Create permit record
   → Generate PDF permit
   → Trigger WhatsApp send (async)
   → Return success + permit

RETURN FIREARM:
1. Find register record by firearm_id
2. Delete from register (or mark returned)
3. Insert into register_history (action='RETURNED')
4. Return success
```

### Routers to build

#### `/api/register`
- `GET /` — current register (all active issuances)
- `GET /guard/{guard_id}` — what a specific guard currently has
- `POST /issue` — issue firearm (runs full issuance logic)
- `POST /return` — return firearm

#### `/api/register/history`
- `GET /` — full audit trail (filterable by date, guard, firearm)
- `GET /guard/{guard_id}` — history for one guard
- `GET /firearm/{firearm_id}` — history for one firearm

### Tasks
- [ ] Write `issuance.py` service with full validation logic
- [ ] Write register router with all endpoints
- [ ] Write unit tests for issuance validation logic (pytest)
- [ ] Test: double-booking attempt should return 409 error
- [ ] Test: unauthorized guard should return 403 error

---

## Phase 5 — Permit Generation (PDF)

**Goal:** Generate print-ready PDF permits matching existing Excel permit layout.

### Two permit formats
1. **Full Permit** — guard photo, full personal details, firearm details, authorizing officer, date
2. **Mini Permit** — condensed, wallet-size or dashboard format for CRT vehicle

### Tasks
- [ ] Study `Excel_Sample/Firearms Permit.xlsm` Permit and Mini Permit sheets for exact layout
- [ ] Create HTML/CSS permit templates in `backend/app/templates/permit_full.html` and `permit_mini.html`
- [ ] Write `backend/app/services/permit_generator.py` using WeasyPrint to render HTML → PDF
- [ ] Store generated PDFs in `backend/permits/` folder (gitignored)
- [ ] Auto-generate permit number: format `BC-YYYYMMDD-NNNN`
- [ ] Trigger permit generation as part of issuance flow
- [ ] Add endpoint: `GET /api/permits/{id}/download` — returns PDF

---

## Phase 6 — Authentication & Role-Based Access

**Goal:** Secure login, JWT tokens, superuser vs read-only access control.

### Roles
- **Superuser** — full access: can create guards/firearms, issue/return, manage system
- **Operator** — can issue/return firearms, view register (future phase if needed)

### Tasks
- [ ] Create `backend/app/core/auth.py` — JWT creation and verification
- [ ] Create `backend/app/core/security.py` — password hashing (bcrypt)
- [ ] Build `/api/auth/login` endpoint — returns access token
- [ ] Build `get_current_user` dependency for protected routes
- [ ] Apply auth dependency to all routes except `/health` and `/auth/login`
- [ ] Create first superuser via a setup script or seeding endpoint
- [ ] Store token in frontend (localStorage or httpOnly cookie — httpOnly preferred)

---

## Phase 7 — WhatsApp Integration (Twilio)

**Goal:** Auto-send permit PDF to CRT vehicle WhatsApp number on issuance.

### Flow
1. Firearm issued → permit PDF generated
2. CRT vehicle number pulled from permit/guard record
3. Twilio API called: send WhatsApp message with PDF attachment
4. `permits.whatsapp_sent` and `whatsapp_sent_at` updated

### Tasks
- [ ] Set up Twilio account, enable WhatsApp sandbox (or production number)
- [ ] Add Twilio credentials to `.env`
- [ ] Write `backend/app/services/whatsapp.py` — send PDF via Twilio
- [ ] Run WhatsApp send as a background task (FastAPI `BackgroundTasks`) — don't block the issuance response
- [ ] Handle send failures gracefully — log error, set `whatsapp_sent = false`, allow manual retry
- [ ] Add endpoint: `POST /api/permits/{id}/resend-whatsapp` — manual retry

---

## Phase 8 — Frontend: React Screens

**Goal:** Full browser UI for all system functions. No installation needed for end users.

### Screens to build

| Screen | Route | Access |
|--------|-------|--------|
| Login | `/login` | Public |
| Dashboard | `/` | All |
| Guards List | `/guards` | Superuser |
| Guard Detail / Edit | `/guards/:id` | Superuser |
| Add Guard | `/guards/new` | Superuser |
| Firearms List | `/firearms` | Superuser |
| Add / Edit Firearm | `/firearms/new`, `/firearms/:id` | Superuser |
| Issue Firearm | `/issue` | All |
| Return Firearm | `/return` | All |
| Current Register | `/register` | All |
| Register History | `/history` | All |
| Permits | `/permits` | All |
| Permit Detail + Print | `/permits/:id` | All |
| System Admin | `/admin` | Superuser |

### Component structure
```
src/
├── pages/         ← one file per screen
├── components/    ← reusable: Table, Modal, Badge, Sidebar, etc.
├── api/           ← axios functions per resource (guards.js, firearms.js, etc.)
├── context/       ← AuthContext (stores JWT, current user)
└── App.jsx        ← router setup with protected routes
```

### Tasks
- [ ] Set up React Router with protected route wrapper
- [ ] Build AuthContext + login page + token handling
- [ ] Build shared layout: sidebar nav + top bar
- [ ] Build Dashboard screen (counters: active guards, firearms out, today's issuances)
- [ ] Build Guards screens (list with search/filter, add/edit form, permissions matrix)
- [ ] Build Firearms screens (list with availability status badges)
- [ ] Build Issue Firearm screen — guard selector → firearm selector → validate → confirm
- [ ] Build Return Firearm screen — show currently issued, select to return
- [ ] Build Register screen — live table of current issuances
- [ ] Build Register History screen — filterable audit log
- [ ] Build Permits screen — list + individual download/print + resend WhatsApp

---

## Phase 9 — Reporting & SAPS Exports

**Goal:** Weekly/monthly reports and SAPS-compliant audit exports.

### Reports
- Current register snapshot (all active issuances)
- Historical register for date range
- Guard activity report (all firearms a guard has carried)
- Firearm usage report

### Tasks
- [ ] Build `GET /api/reports/register` — current snapshot, exportable as CSV or Excel
- [ ] Build `GET /api/reports/history` — date-range audit export
- [ ] Use `openpyxl` to generate Excel exports
- [ ] Add export buttons to History screen in frontend

---

## Phase 10 — Testing & QA

### Unit Tests (pytest)
- [ ] Issuance validation: authorization check
- [ ] Issuance validation: double-booking block
- [ ] Permit number generation
- [ ] JWT token creation/verification

### Integration Tests
- [ ] Full issuance flow: issue → record in register → history entry → permit created
- [ ] Return flow: return → removed from register → history entry
- [ ] Auth: protected route rejects unauthenticated request

### Manual QA Checklist
- [ ] Can create a guard with permissions
- [ ] Can issue firearm to authorized guard
- [ ] Double-booking blocked with correct error message
- [ ] Unauthorized guard blocked with correct error message
- [ ] Permit PDF downloads correctly
- [ ] WhatsApp sends on issuance
- [ ] Register history shows correct entries
- [ ] Soft-deleted guard cannot receive firearms
- [ ] SAPS export generates correct Excel file

---

## Phase 11 — Internal Network Deployment

**Goal:** Run on a single Windows LAN server, accessible from any browser on the network.

### Architecture (on-premises)
```
[LAN Workstations] ──browser──▶ [Windows Server :80]
                                      │
                          ┌───────────┴───────────┐
                     Nginx (reverse proxy)         │
                          │                        │
                   React build              FastAPI :8000
                   (static files)          (uvicorn/gunicorn)
                                                   │
                                            PostgreSQL :5432
```

### Tasks
- [ ] Build React frontend: `npm run build` → output to `dist/`
- [ ] Install Nginx for Windows (or use IIS as reverse proxy)
- [ ] Configure Nginx to serve React `dist/` on port 80 and proxy `/api/` to FastAPI on port 8000
- [ ] Run FastAPI with Gunicorn (Windows: use `uvicorn` with multiple workers via `--workers 4`)
- [ ] Create Windows service for FastAPI using NSSM (Non-Sucking Service Manager)
- [ ] Configure PostgreSQL to only accept local connections (no external exposure)
- [ ] Set `CORS_ORIGINS` in backend `.env` to the server's LAN IP only
- [ ] Set up daily PostgreSQL backup script (pg_dump to local folder)
- [ ] Test from another machine on the LAN

### Production `.env` additions
```
CORS_ORIGINS=http://192.168.x.x
ENVIRONMENT=production
PDF_STORAGE_PATH=C:\sites\BallistiCore\permits\
```

---

## Build Order Summary

| Phase | What Gets Built | Deliverable |
|-------|----------------|-------------|
| 1 | Scaffold + DB connection | Backend health check + DB live |
| 2 | Schema + migrations | All tables in PostgreSQL |
| 3 | CRUD API | Guards, firearms, permissions endpoints |
| 4 | Issuance engine | Issue/return with full validation |
| 5 | PDF permits | Downloadable permit PDFs |
| 6 | Auth | Login, JWT, protected routes |
| 7 | WhatsApp | Auto-send permit on issuance |
| 8 | Frontend | Full React UI |
| 9 | Reporting | SAPS exports |
| 10 | Testing | QA sign-off |
| 11 | Deployment | Live on LAN |

---

*Reference: `Excel_Sample/Firearms Permit.xlsm` — source of truth for data structure and permit layout. Never modify.*
