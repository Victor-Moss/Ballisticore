# BallistiCore — Phase 12 Expansion Plan

> Created: 2026-03-30
> Based on: analysis of `Excel_Sample/Firearms Permit.xlsm` (all 10 sheets) + Excel Add User screenshot

---

## Overview

Phase 12 expands BallistiCore to match the full feature set of the Excel workbook. The expansion covers four areas:

1. **User management** — granular permission booleans, weapon-category permissions, additional profile fields
2. **Guard model** — SAPS competency tracking per weapon type, region, personnel number, CIT routes
3. **Permit model** — ammunition tracking, separate time fields, CIT routing, witness, return inspection fields
4. **Register model** — ammunition, inspection flags, signature fields, CIT/responsible person

Each section lists the database changes, backend changes, and frontend changes needed.

---

## Part 1 — User Management Expansion

### What the Excel has (System Admin sheet)

The Excel "Add User" dialog has the following fields not currently in BallistiCore:

**Profile fields:**
- `personnel_number` — employee ID
- `psira_number` — PSIRA registration number
- `competency` — competency certification
- `phone_number` — contact number
- `id_number` — national ID

**12 granular permission booleans:**
| Column | What it controls |
|--------|-----------------|
| `perm_new_permits` | Can issue firearms |
| `perm_return_permits` | Can return firearms |
| `perm_manage_weapons` | Can add/edit firearms |
| `perm_manage_staff` | Can add/edit guards |
| `perm_access_database` | Can view register + history |
| `perm_send_whatsapp` | Can trigger WhatsApp sends |
| `perm_view_register_history` | Can access Register History page |
| `perm_system_admin` | Full system admin access |
| `perm_add_user` | Can create new users |
| `perm_modify_user` | Can edit existing users |
| `perm_change_passwords` | Can reset user passwords |
| `perm_clear_logs` | Can clear/purge logs |

**4 weapon-category permissions:**
| Column | What it controls |
|--------|-----------------|
| `perm_carbine` | Authorised to manage carbine-type firearms |
| `perm_handgun` | Authorised to manage handgun-type firearms |
| `perm_rifle` | Authorised to manage rifle-type firearms |
| `perm_shotgun` | Authorised to manage shotgun-type firearms |

### Database changes

**Migration: add to `users` table**
```python
# New columns on User model
personnel_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
psira_number:     Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
competency:       Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
phone_number:     Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
id_number:        Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

# Granular permissions (all default False)
perm_new_permits:          Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_return_permits:       Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_manage_weapons:       Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_manage_staff:         Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_access_database:      Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_send_whatsapp:        Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_view_register_history:Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_system_admin:         Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_add_user:             Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_modify_user:          Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_change_passwords:     Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_clear_logs:           Mapped[bool] = mapped_column(Boolean, server_default='false')

# Weapon category permissions
perm_carbine: Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_handgun: Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_rifle:   Mapped[bool] = mapped_column(Boolean, server_default='false')
perm_shotgun: Mapped[bool] = mapped_column(Boolean, server_default='false')
```

> **Note:** `is_admin` remains — it acts as a superuser override. Admin users bypass granular permission checks. Non-admin users are controlled by the granular booleans.

### Backend changes

**`schemas/user.py`**
- Add all new fields to `UserCreate`, `UserUpdate`, and `UserOut`
- `UserUpdate` — partial update (all fields optional)

**`routers/auth.py`**
- Add `PUT /api/users/{id}` — update user profile + permissions (requires `perm_modify_user` or `is_admin`)
- Add `PUT /api/users/{id}/password` — reset another user's password (requires `perm_change_passwords` or `is_admin`)
- Add `PUT /api/users/{id}/deactivate` and `reactivate` endpoints (already exists, confirm it's there)

**`core/auth.py`**
- Add helper dependencies: `require_perm_manage_staff`, `require_perm_new_permits`, etc.
- Pattern: check `is_admin OR perm_xxx`

**`services/users.py`**
- Update `create()` to accept all new fields
- Add `update()` service function

### Frontend changes

**`src/pages/Admin.jsx`** (already exists — user management page)
- Expand "Add User" modal to match the Excel dialog layout:
  - Profile section: username, password, email, phone_number, personnel_number, psira_number, competency, id_number
  - Permissions section: 12 boolean checkboxes in a grid (labelled as in the table above)
  - Weapon types section: 4 boolean checkboxes (Carbine, Handgun, Rifle, Shotgun)
- Add "Edit User" view with same fields (password field optional — only set if filled in)
- Deactivate/Reactivate buttons per user row

**`src/pages/` — gate pages by permission**
- Issue firearm page: check `perm_new_permits`
- Return page: check `perm_return_permits`
- Firearms pages: check `perm_manage_weapons`
- Guards pages: check `perm_manage_staff`
- History page: check `perm_view_register_history`
- Admin page: check `perm_system_admin` or `is_admin`

---

## Part 2 — Guard Model Expansion

### What the Excel has (Guards sheet)

**Profile fields not yet in BallistiCore:**
- `region` — geographic region (string)
- `personnel_number` — employee number

**SAPS competency per weapon type (8 fields):**
| Field | Description |
|-------|-------------|
| `saps_comp_carbine` | SAPS competency number for carbines |
| `saps_expiry_carbine` | Expiry date of carbine competency |
| `saps_comp_handgun` | SAPS competency number for handguns |
| `saps_expiry_handgun` | Expiry date of handgun competency |
| `saps_comp_rifle` | SAPS competency number for rifles |
| `saps_expiry_rifle` | Expiry date of rifle competency |
| `saps_comp_shotgun` | SAPS competency number for shotguns |
| `saps_expiry_shotgun` | Expiry date of shotgun competency |

**Weapon-type flags (4 booleans):**
- `permitted_carbine` — guard is cleared to carry carbines
- `permitted_handgun` — guard is cleared to carry handguns
- `permitted_rifle` — guard is cleared to carry rifles
- `permitted_shotgun` — guard is cleared to carry shotguns

**CIT routes — new table:**
Guards can be assigned to multiple CIT (Cash-In-Transit) routes. Each route has a name and a cell phone number.

### Database changes

**Migration: add to `guards` table**
```python
region:            Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
personnel_number:  Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

saps_comp_carbine:    Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
saps_expiry_carbine:  Mapped[Optional[date]] = mapped_column(Date, nullable=True)
saps_comp_handgun:    Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
saps_expiry_handgun:  Mapped[Optional[date]] = mapped_column(Date, nullable=True)
saps_comp_rifle:      Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
saps_expiry_rifle:    Mapped[Optional[date]] = mapped_column(Date, nullable=True)
saps_comp_shotgun:    Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
saps_expiry_shotgun:  Mapped[Optional[date]] = mapped_column(Date, nullable=True)

permitted_carbine: Mapped[bool] = mapped_column(Boolean, server_default='false')
permitted_handgun: Mapped[bool] = mapped_column(Boolean, server_default='false')
permitted_rifle:   Mapped[bool] = mapped_column(Boolean, server_default='false')
permitted_shotgun: Mapped[bool] = mapped_column(Boolean, server_default='false')
```

**New table: `guard_cit_routes`**
```python
class GuardCITRoute(Base):
    __tablename__ = "guard_cit_routes"
    id:         Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    guard_id:   Mapped[str] = mapped_column(ForeignKey("guards.id"), nullable=False)
    route_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cell_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guard:      Mapped["Guard"] = relationship(back_populates="cit_routes")
```

### Backend changes

**`models/guard.py`** — add new columns + relationship to GuardCITRoute
**`models/guard_cit_route.py`** — new model file

**`schemas/guard.py`**
- Add new fields to `GuardCreate`, `GuardUpdate`, `GuardOut`
- Add `GuardCITRouteCreate`, `GuardCITRouteOut` schemas

**`routers/guards.py`**
- Add `GET /api/guards/{id}/cit-routes`
- Add `POST /api/guards/{id}/cit-routes`
- Add `DELETE /api/guards/{id}/cit-routes/{route_id}`

**`services/guards.py`** — add CIT route CRUD functions

### Frontend changes

**`src/pages/GuardDetail.jsx`** — expand form:
- Add section: Profile (region, personnel_number)
- Add section: SAPS Competency (4 weapon types × 2 fields = 8 inputs in a grid)
- Add section: Weapon Type Clearance (4 checkboxes)
- Add section: CIT Routes — list of existing routes with add/delete controls

---

## Part 3 — Permit Model Expansion

### What the Excel has (Permit sheet)

Fields found in the Excel permit but missing from BallistiCore:

| Field | Description |
|-------|-------------|
| `rounds_issued` | Ammunition rounds issued with the firearm |
| `rounds_returned` | Ammunition rounds returned |
| `period_from_time` | Time component of `period_from` |
| `valid_until_time` | Time component of `valid_until` |
| `posted` | Boolean — was permit posted to SAPS? |
| `cit_cell_route` | CIT route assigned to this permit |
| `witness` | Name of the witness at issuance |
| `firearm_returned_correct` | Boolean — firearm returned in correct condition |
| `in_order` | Boolean — all paperwork in order |
| `remarks` | Free-text remarks on the permit |
| `saps_competency_number` | Guard's SAPS competency number at time of issue |

### Database changes

**Migration: add to `permits` table**
```python
rounds_issued:            Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
rounds_returned:          Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
period_from_time:         Mapped[Optional[time]] = mapped_column(Time, nullable=True)
valid_until_time:         Mapped[Optional[time]] = mapped_column(Time, nullable=True)
posted:                   Mapped[bool]           = mapped_column(Boolean, server_default='false')
cit_cell_route:           Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
witness:                  Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
firearm_returned_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
in_order:                 Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
remarks:                  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
saps_competency_number:   Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
```

### Backend changes

**`schemas/register.py`** — add new permit fields to `IssueRequest` and permit-related schemas
**`services/issuance.py`** — capture `rounds_issued`, `saps_competency_number`, `witness` on issue; capture `rounds_returned`, `firearm_returned_correct`, `in_order`, `remarks` on return
**`services/permit_generator.py`** — include new fields in PDF layout (ammunition, witness, remarks)

### Frontend changes

**`src/pages/IssueFirearm.jsx`** — add optional fields:
- Rounds issued (number input)
- CIT route (text or dropdown)
- Witness name
- SAPS competency number (auto-populated from guard's record)
- Period from/until times (time pickers alongside existing date pickers)

**`src/pages/ReturnFirearm.jsx`** — add return inspection fields:
- Rounds returned
- Firearm returned correct (checkbox)
- In order (checkbox)
- Remarks (textarea)

---

## Part 4 — Register Model Expansion

### What the Excel has (Register / Database sheets)

Fields found in the Excel register but missing from BallistiCore:

| Field | Description |
|-------|-------------|
| `ammunition_issued` | Rounds issued (mirrors permit) |
| `ammunition_returned` | Rounds returned (mirrors permit) |
| `firearm_inspected_correct` | Boolean — firearm condition on issue |
| `firearm_returned_correct` | Boolean — firearm condition on return |
| `permit_returned` | Boolean — physical permit handed back |
| `guard_signature` | Signature field (path to image or base64) |
| `authorising_officer_signature` | Officer's signature |
| `audit_signature` | Audit/SAPS officer's signature |
| `cit_id` | CIT route identifier |
| `responsible_person_name` | Name of responsible officer |

### Database changes

**Migration: add to `register` and `register_history` tables**
```python
# Add to register (active issuances)
ammunition_issued:           Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
firearm_inspected_correct:   Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
cit_id:                      Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
responsible_person_name:     Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)

# Add to register_history (audit trail)
ammunition_issued:           Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
ammunition_returned:         Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
firearm_inspected_correct:   Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
firearm_returned_correct:    Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
permit_returned:             Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
guard_signature:             Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
authorising_officer_signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
audit_signature:             Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
cit_id:                      Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
responsible_person_name:     Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
```

### Backend changes

**`schemas/register.py`** — add new fields to `IssueRequest`, `ReturnRequest`, `RegisterEntryOut`, `HistoryEntryOut`
**`services/issuance.py`** — persist new fields on issue and return

### Frontend changes

**`src/pages/IssueFirearm.jsx`** — add: ammunition quantity, responsible person name, CIT ID
**`src/pages/ReturnFirearm.jsx`** — add: ammunition returned, permit returned checkbox, inspection checkboxes
**`src/pages/Register.jsx`** — show ammunition column
**`src/pages/History.jsx`** — show ammunition + inspection columns

---

## Part 5 — Firearm Model Expansion

### What the Excel has (Lists sheet)

The Lists/Database sheets reference a weapon `type` category field not currently on the Firearm model:

| Field | Description |
|-------|-------------|
| `firearm_type` | Category: Carbine / Handgun / Rifle / Shotgun |

This is needed to:
- Link firearm to guard's weapon-type clearances (`permitted_carbine`, etc.)
- Link to user's weapon-category permissions (`perm_carbine`, etc.)
- Validate issuance: guard must have clearance for this weapon type

### Database changes

**Migration: add to `firearms` table**
```python
firearm_type: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True
)
# Values: 'carbine', 'handgun', 'rifle', 'shotgun'
```

### Backend changes

**`services/issuance.py`** — add validation step: if firearm has a type set, check guard has matching `permitted_xxx` flag

### Frontend changes

**`src/pages/FirearmDetail.jsx`** — add `firearm_type` dropdown (Carbine / Handgun / Rifle / Shotgun / Unspecified) to editable fields

---

## Implementation Order

These are independent enough to tackle in any order, but the recommended sequence is:

| Step | Task | Reason |
|------|------|--------|
| 12a | User management expansion | Highest priority — matches the screenshot request |
| 12b | Guard model expansion | SAPS compliance fields — needed for accurate permits |
| 12c | Firearm type field | Small change, unlocks weapon-type validation |
| 12d | Permit model expansion | Depends on guard competency fields being in place |
| 12e | Register model expansion | Depends on permit changes being stable |

Each step follows the same pattern:
1. Update SQLAlchemy model
2. Generate and apply Alembic migration
3. Update Pydantic schemas
4. Update service functions
5. Update router (add/update endpoints)
6. Update frontend pages
7. Run tests (`pytest`)

---

## Migration Naming Convention

Follow the existing pattern:
```
alembic revision --autogenerate -m "add_user_permissions_fields"
alembic revision --autogenerate -m "add_guard_competency_fields"
alembic revision --autogenerate -m "add_guard_cit_routes_table"
alembic revision --autogenerate -m "add_firearm_type"
alembic revision --autogenerate -m "add_permit_ammunition_fields"
alembic revision --autogenerate -m "add_register_inspection_fields"
```

All new boolean columns must use `server_default='false'` in the migration file to avoid NOT NULL violations on existing rows.
All new nullable columns can be added without a server_default.
