# BallistiCore — Permissions Enforcement Map

A living reference mapping every checkbox on the **Add / Modify User** screen
(Admin → Users) to what it actually controls in the UI **and** on the backend.

**Current invariant (keep it true):** every checkbox on this screen is enforced
on both the frontend and the backend. There are no UI-only gates and no dead
checkboxes. When you add a new `perm_*` flag, add a backend
`require_permission(...)` check for it *and* a section here, or don't ship the
checkbox.

- **Checkbox → flag** definitions: `BallistiCore_app/frontend/src/pages/Admin.jsx:25-37` (`PERMISSION_LABELS`)
- **Flag storage**: `BallistiCore_app/backend/app/models/user.py:26-37`
- **Core gate helpers** (`BallistiCore_app/backend/app/core/auth.py`):
  - `is_super_admin(user)` → `is_admin OR perm_system_admin` (`auth.py:54-59`)
  - `require_admin` → super admin only (`auth.py:45-51`)
  - `require_permission(*keys)` → super admin **or** holds at least one key (`auth.py:62-80`)
  - `require_change_passwords` → `is_super_admin(user) OR perm_change_passwords` (`auth.py:83-91`)
- **Frontend gate helpers** (`BallistiCore_app/frontend/src/utils/permissions.js`):
  `hasPerm`, `isSuperAdmin`, `canAccessAdmin`, `ADMIN_SECTION_PERMS`

## Change history

- **2026-06-18 — Full enforcement pass:**
  - Closed the two UI-only gaps: **Access Register** (`perm_access_database`) and
    **View History** (`perm_view_register_history`) are now enforced on every
    register/history read endpoint (direct API + report exports).
  - Removed five dead checkboxes — **Clear Logs** and the four **Weapon
    Categories** (Carbine/Handgun/Rifle/Shotgun) — from the UI, from
    `ADMIN_SECTION_PERMS`, from the API schemas/model, and dropped their DB
    columns (migration `b7d4e9a1c2f3`).
  - Fixed `require_change_passwords` to use `is_super_admin` instead of the bare
    `is_admin` flag.
  - **No backfill** was applied (deliberate): of 13 users, only 1 active
    non-admin (`limited_a1ec07`) lost incidental Register/History access; it must
    now be granted explicitly. Super admins are unaffected.
  - Label audit: all 11 remaining labels were verified against their enforced
    scope. No renames were required.

---

## ✅ Final state — 11 checkboxes, all enforced both sides

| # | Checkbox | Flag | What it genuinely controls |
|---|---|---|---|
| 1 | Issue Permits | `perm_new_permits` | Issuing a firearm (creates a permit) |
| 2 | Return Permits | `perm_return_permits` | Returning an issued firearm |
| 3 | Manage Firearms | `perm_manage_weapons` | Create / edit / delete firearms |
| 4 | Manage Guards | `perm_manage_staff` | Create / edit / (de)activate / delete guards + CIT routes |
| 5 | Access Register | `perm_access_database` | Viewing the current register (UI + API + Excel export) |
| 6 | Send WhatsApp | `perm_send_whatsapp` | Resending a permit via WhatsApp |
| 7 | View History | `perm_view_register_history` | Viewing issue/return history (UI + API + Excel exports) |
| 8 | System Admin | `perm_system_admin` | Master override; system-management admin features |
| 9 | Add Users | `perm_add_user` | Creating operator accounts |
| 10 | Modify Users | `perm_modify_user` | Editing / (de)activating operator accounts |
| 11 | Change Passwords | `perm_change_passwords` | Managing guard sign-in accounts + changing user passwords |

**Removed (dead, deleted):** Clear Logs, Carbine, Handgun, Rifle, Shotgun.

---

## Permissions

### 1. Issue Permits — `perm_new_permits`
- **Frontend:** nav item "Issue Firearm" `components/Layout.jsx:34`; route `/issue` `App.jsx:69`; co-gates "Permits" nav/route (OR with `perm_send_whatsapp`) `Layout.jsx:37`, `App.jsx:72`.
- **Backend:** `POST /api/register/issue` → `require_permission("perm_new_permits")` `routers/register.py:34`.
- **Label vs scope:** ✅ Issuing a firearm produces a permit — label is domain-accurate.

### 2. Return Permits — `perm_return_permits`
- **Frontend:** nav "Return Firearm" `Layout.jsx:35`; route `/return` `App.jsx:70`.
- **Backend:** `POST /api/register/return` → `require_permission("perm_return_permits")` `routers/register.py:58`.
- **Label vs scope:** ✅

### 3. Manage Firearms — `perm_manage_weapons`
- **Frontend:** nav "Firearms" `Layout.jsx:39`; routes `/firearms`, `/firearms/:id` `App.jsx:75-76`.
- **Backend:** `POST /api/firearms/` `routers/firearms.py:34`, `PUT /api/firearms/{id}` `:42`, `DELETE /api/firearms/{id}` `:54` — all `require_permission("perm_manage_weapons")`. (GET reads open to any session by design.)
- **Label vs scope:** ✅ (`weapons` flag = firearms feature.)

### 4. Manage Guards — `perm_manage_staff`
- **Frontend:** nav "Guards" `Layout.jsx:38`; routes `/guards`, `/guards/:id` `App.jsx:73-74`.
- **Backend:** guard create/update/deactivate/reactivate/delete + CIT routes — `require_permission("perm_manage_staff")` at `routers/guards.py:40,55,64,75,89,171,180`.
- **Label vs scope:** ✅ (`staff` flag = guards feature.)

### 5. Access Register — `perm_access_database`  *(gap closed)*
- **Frontend:** nav "Register" `Layout.jsx:33`; route `/register` `App.jsx:68`.
- **Backend:** `GET /api/register/` and `GET /api/register/guard/{id}` → `require_permission("perm_access_database")` `routers/register.py:16,22`; `GET /api/reports/register` (Excel export) → same `routers/reports.py:19`.
- **Label vs scope:** ✅ Controls viewing the register. Independent of View History (verified by test).

### 6. Send WhatsApp — `perm_send_whatsapp`
- **Frontend:** `canSendWhatsapp` `pages/Permits.jsx:8`; "WhatsApp" button gated `Permits.jsx:81`; co-gates "Permits" nav/route `Layout.jsx:37`, `App.jsx:72`.
- **Backend:** `POST /api/permits/{id}/resend-whatsapp` → `require_permission("perm_send_whatsapp")` `routers/permits.py:113`.
- **Label vs scope:** ✅

### 7. View History — `perm_view_register_history`  *(gap closed)*
- **Frontend:** nav "History" `Layout.jsx:36`; route `/history` `App.jsx:71`.
- **Backend:** `GET /api/register/history`, `.../history/guard/{id}`, `.../history/firearm/{id}` → `require_permission("perm_view_register_history")` `routers/register.py:75,87,95`; `GET /api/reports/history` `routers/reports.py:32` and `GET /api/reports/guard/{id}` (per-guard activity = history) `routers/reports.py:51` → same.
- **Label vs scope:** ✅

### 8. System Admin — `perm_system_admin`
- **Frontend:** `isSuperAdmin` = `is_admin || perm_system_admin` `permissions.js:10-12`; gates the system-management Admin tabs (Ammunition, Import, Export, Company Details); System-Admin checkbox locked unless editor is a super admin `Admin.jsx:344`.
- **Backend:** short-circuits `require_admin` (`auth.py:46`) and `require_permission` (`auth.py:71`), so it gates everything those protect (Ammunition mutations, Branding, Import, Export). Escalation clamps: only a super admin may grant `is_admin`/`perm_system_admin` `routers/auth.py:44-46,85-87`.
- **Label vs scope:** ✅ (master override.)

### 9. Add Users — `perm_add_user`
- **Frontend:** `canAdd` `Admin.jsx:74`; "+ Add User" button `Admin.jsx:202`; in `ADMIN_SECTION_PERMS` `permissions.js:29`.
- **Backend:** `POST /api/auth/users` → `require_permission("perm_add_user")` `routers/auth.py:39`; also accepted (OR) for `GET /api/auth/users` `:62`.
- **Label vs scope:** ✅

### 10. Modify Users — `perm_modify_user`
- **Frontend:** `canModify` `Admin.jsx:75`; Edit button `Admin.jsx:182`; Deactivate/Reactivate `Admin.jsx:185`; field-lock on edit `Admin.jsx:126`; in `ADMIN_SECTION_PERMS` `permissions.js:30`.
- **Backend:** `PUT /api/auth/users/{id}` (OR with change_passwords) `routers/auth.py:72`; `PUT .../deactivate` `:99`; `PUT .../reactivate` `:116`.
- **Label vs scope:** ✅

### 11. Change Passwords — `perm_change_passwords`
- **Frontend:** `canChangePw` `Admin.jsx:76`; reveals password field on edit (`showPasswordField` `Admin.jsx:127`); contributes to Edit-button visibility `Admin.jsx:182`; in `ADMIN_SECTION_PERMS` `permissions.js:31`; guard sign-in account card in `pages/GuardDetail.jsx`.
- **Backend:** `require_change_passwords` (= `is_super_admin OR perm_change_passwords`, `auth.py:83-91`) gates guard account endpoints `POST/PUT/DELETE /api/guards/{id}/account[...]` `routers/guards.py:110,131,152`; also accepted (OR) on user create/list/update `routers/auth.py:62,72`.
- **Label vs scope:** ✅ Covers changing guard-login passwords and user passwords. **Fixed 2026-06-18:** previously used the bare `is_admin` flag, so a `perm_system_admin`-only super admin was wrongly excluded; now uses `is_super_admin`.

---

## Removed checkboxes (no longer exist)

These were deleted from the UI and code on 2026-06-18 and their DB columns
dropped (migration `b7d4e9a1c2f3`). Documented here so the history is clear.

- **Clear Logs** (`perm_clear_logs`) — no log-clearing feature ever existed; the
  flag's only effect was incidentally granting Admin-section entry via
  `ADMIN_SECTION_PERMS`. Removed from the UI and from `ADMIN_SECTION_PERMS`.
- **Carbine / Handgun / Rifle / Shotgun** (`perm_carbine` etc.) — operator-level
  weapon-category flags that were read nowhere. (Weapon-type clearance at issue
  time is enforced against the **guard's** `permitted_<type>` field —
  `services/issuance.py:84-89` — which is unrelated and remains in place.)

---

## Design notes

- **Read endpoints are gated where a checkbox claims to control them.** Register
  and History reads are now behind their flags. Other read endpoints (firearms
  list, guards list, permits list, dashboard stats) remain open to any logged-in
  user — there is no checkbox claiming to gate them, so that is not a mismatch.
- **DB columns were dropped, not left unused.** Keeping orphaned `NOT NULL`
  boolean columns that nothing reads is exactly the cruft this pass removed; the
  data had no value, and the migration's `downgrade()` re-creates them if needed.
