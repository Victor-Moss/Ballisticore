# Building the BallistiCore self-hosted installer

This produces a single `BallistiCore-Setup-<version>.exe` that installs a
fully offline, single-machine deployment of BallistiCore on Windows.

## Architecture (what gets installed)

```
<install folder>\
├─ python\        Bundled relocatable CPython 3.12 + backend dependencies
├─ pgsql\         Bundled portable PostgreSQL (binaries only)
├─ backend\       FastAPI app. Serves BOTH the JSON API and the React UI.
│   └─ .env       Generated at install (DB password, secret key, paths)
├─ frontend\      Built React app (static files, served by the backend)
├─ pgdata\        PostgreSQL data directory  ← created on first run (LOCAL DATA)
├─ permits\       Generated permit PDFs       ← created on first run
├─ logs\          setup / postgres logs
├─ config\        Generated secrets (db passwords)
├─ scripts\       _env, init_db, start_all, stop_all
├─ BallistiCore.bat          Launcher (start + open browser)
└─ Stop BallistiCore.bat     Stop everything
```

There is **one** web process: the FastAPI backend (uvicorn) serves the API
*and* the compiled React UI from the same origin on `http://localhost:8000`
(enabled by the `FRONTEND_DIST` setting). No nginx, no Node at runtime.
PostgreSQL runs as a local process owned by the installing user — no Windows
service, no admin rights, and its data never leaves the folder.

## Prerequisites on the build machine

- Windows x64
- [Node.js](https://nodejs.org) 20+ (to build the frontend)
- [Inno Setup 6.3+](https://jrsoftware.org/isdl.php) (the script uses the
  `x64compatible` architecture identifier, added in 6.3)
- PowerShell 5+

## Step 1 — Supply the two bundled runtimes

These are large third-party binaries, so they are **not** committed. Drop them
into `installer\payload\` yourself:

### a) Python → `installer\payload\python\`
Use a *relocatable* CPython 3.12 (x64). Recommended:
[python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases).
Download the asset named like
`cpython-3.12.*+*-x86_64-pc-windows-msvc-install_only.tar.gz`, extract it, and
copy its **contents** so that this path exists:

```
installer\payload\python\python.exe
```

(The official "Windows embeddable" zip also works but needs its `._pth`
edited to enable site-packages — python-build-standalone avoids that hassle.)

### b) PostgreSQL → `installer\payload\pgsql\`
Download the PostgreSQL **binaries ZIP** (not the installer) for Windows
x86-64 from
[enterprisedb.com/download-postgresql-binaries](https://www.enterprisedb.com/download-postgresql-binaries)
(PostgreSQL 16 or 17). Extract it; it contains a `pgsql\` folder. Copy that so
this path exists:

```
installer\payload\pgsql\bin\pg_ctl.exe
```

## Step 2 — Stage the payload

From `installer\`:

```powershell
powershell -ExecutionPolicy Bypass -File build_payload.ps1
```

This builds the frontend, copies the backend, and pip-installs the backend's
runtime dependencies (`requirements-runtime.txt`) into the bundled Python. It
fails fast with instructions if either runtime from Step 1 is missing.

## Step 3 — Compile the installer

Open `BallistiCore.iss` in Inno Setup and press **Compile** (F9), or:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" BallistiCore.iss
```

> Inno Setup's install location varies. If the path above doesn't exist, it may
> be at `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` (system-wide install)
> instead of `%LOCALAPPDATA%\Programs\Inno Setup 6\` (per-user install).

The result is `installer\dist\BallistiCore-Setup-1.0.0.exe`. Ship that single
file to the client; see `README.txt` for their setup steps.

## Versioning / branding

- Bump `AppVersion` at the top of `BallistiCore.iss`.
- Default company branding is collected in the install wizard and written to
  `backend\branding.json`; the operator can change it later under
  **Admin → Company Details**.
- **Never commit a modified `backend\branding.json`.** It must ship with the
  defaults (`"Your Company Name"`, `setup_completed: false`), or a fresh install
  skips the First-Time Setup wizard and starts with someone else's branding. A
  dev machine that has run the wizard will have local values in that file — check
  `git status` before committing a release.

## Release process — order of operations

Follow this order. It exists so the git history is *evidence* of what was
verified, not just a claim about it.

1. **Cut the release** — one commit bumping `AppVersion`, updating the README
   download link / feature highlights / releases-table row, and the ROADMAP's
   shipped-version line. The releases-table row starts as
   `· installer build pending`.
2. **Build** the payload and compile the installer (Steps 2–3 above). Re-run
   `build_payload.ps1` even if `payload\` looks populated — it goes stale
   silently, and a stale payload produces an installer that does not contain
   the release you are shipping. Confirm a known new symbol is present in
   `payload\backend` before compiling.
3. **Smoke-test** the compiled `Setup.exe` (see *Verification status* below for
   the checklist).
4. **Only if the smoke test passes**, commit the marker flipping that row to
   `· installer smoke-tested ✅`.
5. Merge the release PR, push the annotated tag, publish the GitHub Release with
   the `Setup.exe` attached and its SHA-256 in the body.

**Do not author the "smoke-tested" marker before the smoke test has run.** It is
tempting to pre-stage it so the release closes in a single action, and both the
1.6.0 and 1.8.0 releases did exactly that. In each case the test did pass before
anything was published, so the claim was true — but the commit timestamps sit
*earlier* than the installer they vouch for, and nothing in the history shows the
test happened in between. Anyone auditing later cannot distinguish that from a
marker committed on the assumption it would pass. Committing the marker after the
fact costs one extra commit and makes the ordering self-evidencing.

If the smoke test fails, stop: fix, rebuild, re-test. Do not merge, tag, or
publish a release whose marker is unearned.

## Notes

- **Offline:** once Step 2 has bundled the wheels into `payload\python`, the
  installer needs no internet on the client machine.
- **Data stays local:** the only outbound traffic is optional Twilio WhatsApp
  sends, and only when Twilio credentials are filled into `backend\.env`.
- **Ports:** backend `8000`, PostgreSQL `5433` (loopback only). PostgreSQL
  intentionally uses 5433, not the default 5432, so the bundled instance won't
  collide with any PostgreSQL the client already has. Change them in
  `launcher\scripts\_env.bat` before building if they still clash on the target.
- This supersedes the older nginx + NSSM-services approach in
  `deploy\installer\ArmsRegister.iss`, which is kept only for reference.
- **Shell tip:** run the `ISCC` compile (and `git push`) from a plain Windows
  `cmd`/PowerShell shell. Under MSYS/Git Bash, leading-slash flags can get
  path-mangled (e.g. `/Qp` → a bogus path) — invoke `ISCC.exe BallistiCore.iss`
  without flags, or use `cmd`.

## Verification status

### Smoke-test checklist (run per release, against the compiled `Setup.exe`)

Run from a **clean slate** — uninstall any existing BallistiCore and remove the
leftover install directory first, otherwise first-run DB setup is skipped over an
existing `pgdata` and is not actually exercised. If a working install is present
on the machine, back the whole tree up and verify the copy (file count + total
size) before removing anything.

1. **Silent install** — `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NOCANCEL`;
   expect exit 0 and the correct version registered under
   `HKCU:\...\Uninstall`.
2. **First-run DB setup** — `logs\setup.log` shows `initdb`, role + database
   creation, all Alembic migrations, and `Setup complete.`; `backend\.env` was
   generated with real secrets.
3. **Launcher start** — `BallistiCore.bat`; backend listening on `8000`,
   PostgreSQL on `5433`.
4. **`GET /health`** → **200**.
5. **React UI `GET /`** → **200**.
6. **`POST /api/auth/login`** (`admin`/`admin1234`, form-encoded — the endpoint
   takes `OAuth2PasswordRequestForm`, not JSON) → **200** with a token.
7. **Clean stop** — `Stop BallistiCore.bat`; both ports closed, no stray
   processes.
8. **Uninstall** — exit 0; app files, shortcuts and the registry entry removed.
   `pgdata` and `backend\.env` are *expected to survive* by design, as is any
   `.pyc` bytecode generated after install (Inno only removes what it installed).

Worth also confirming a known new symbol from the release is present in the
*installed* backend, which verifies the shipped binary rather than the source
tree it was built from.

To restore a machine afterwards: reinstall the previous version, then restore
`pgdata` **and** `backend\.env` from the backup. Restoring `pgdata` alone leaves
a broken install — a fresh install generates a new random password for the
`ballisticore_user` role, which will not match the restored cluster.

### Historical results

The **launcher scripts** (`launcher\scripts\*.bat`) were tested end-to-end on
Windows against a throwaway PostgreSQL 17 instance (isolated port + data dir)
driven by the real backend:

- `init_db.bat` — `initdb`, role + database creation, `.env` generation with
  real secrets, and all Alembic migrations applied; Postgres left stopped.
- `start_all.bat` — starts Postgres + the backend; `/health` 200, the React UI
  is served, and `POST /api/auth/login` (admin/admin1234) succeeds. Re-running
  is idempotent (it does not start a second server).
- `stop_all.bat` — stops the backend and Postgres cleanly.

Three bugs were found and fixed during that testing; they are worth knowing if
you edit the scripts:

1. **Secret generation** must not use `for /f` around the Python call — the
   parentheses in `token_hex(16)`/`print(...)` close the `for` group early and
   yield empty secrets. We write to a temp file and read it with `set /p`.
2. **`pg_ctl start` must not redirect to a log we append to again.** The
   launched postmaster inherits that command's stdout handle for its lifetime;
   if it were `setup.log`, every later `>> setup.log` step fails with a sharing
   violation and cmd silently skips the command. It redirects to its own
   `pg_start.log`.
3. **Use `ping -n` for sleeps, not `timeout /t`** — `timeout` errors when stdin
   is redirected / non-interactive (e.g. run by the installer or a launcher).

### Compiled installer (icon build) — full end-to-end test PASSED

The complete pipeline was built and tested on Windows: `build_payload.ps1`
staged a relocatable Python 3.12 + the PostgreSQL 17 binaries + the built
frontend/backend, deps installed into the bundled Python, and `ISCC` compiled
`BallistiCore.iss` cleanly (no warnings) into a ~75 MB `Setup.exe`.

That `Setup.exe` was then silently installed and exercised end-to-end:

- **Branded icon** embedded in `Setup.exe`, installed to `{app}\BallistiCore.ico`,
  and applied to the Start-menu / desktop / Stop shortcuts (`IconLocation`).
- **First-run DB setup ran verbatim** (bundled Python + bundled PostgreSQL on
  port 5433): `initdb`, role/db, `.env` with real secrets, all 11 Alembic
  migrations.
- **Launcher** started the bundled stack and served the app: `/health` 200
  (`production`), React UI 200, `POST /api/auth/login` (admin/admin1234) 200.
- **Stop** shut everything down; **uninstall** removed the app files and
  shortcuts while preserving the data directories (`pgdata`, `.env`).

(The 5433 default — rather than 5432 — was confirmed to let first-run setup
complete on a machine that already has PostgreSQL installed.)
