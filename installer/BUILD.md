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
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" BallistiCore.iss
```

The result is `installer\dist\BallistiCore-Setup-1.0.0.exe`. Ship that single
file to the client; see `README.txt` for their setup steps.

## Versioning / branding

- Bump `AppVersion` at the top of `BallistiCore.iss`.
- Default company branding is collected in the install wizard and written to
  `backend\branding.json`; the operator can change it later under
  **Admin → Company Details**.

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

## Verification status

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

Still **unverified** (requires a Windows build box with the two bundled
runtimes + Inno Setup): `build_payload.ps1`, the bundled-Python dependency
install, and compiling `BallistiCore.iss`. The backend's single-process serving
of the built UI (`FRONTEND_DIST`) was verified separately.
