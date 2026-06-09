# ArmsRegister — Installer Build Guide

> Run these steps on the **build machine** (can be your dev PC).
> The output is a single `ArmsRegister-Setup-1.0.0.exe` in `dist/`.

---

## Prerequisites (install once on the build machine)

1. **Inno Setup 6** — https://jrsoftware.org/isdl.php
2. **Node.js** — https://nodejs.org (for `npm run build`)

---

## What to bundle in `deploy/installer/prereqs/`

Create this folder and drop in:

| Item | Where to get it |
|------|----------------|
| `postgresql-17-windows-x64.exe` | https://www.enterprisedb.com/downloads/postgres-postgresql-downloads |
| `nssm/nssm.exe` | https://nssm.cc/download → extract the zip, take `win64/nssm.exe` |
| `nginx/` (full folder) | https://nginx.org/en/download.html → extract the zip |
| `python/` (embedded Python) | https://www.python.org/downloads/windows/ → **embeddable package (64-bit)** |

> The `nginx.conf.template` placeholder `FRONTEND_PATH` is automatically replaced
> by the installer's [Code] section during `ssPostInstall` — no manual step needed.

### Embedded Python setup (do this once)

The embeddable package has pip disabled by default. Enable it:

```
1. Download python-3.12.x-embed-amd64.zip and extract to prereqs/python/
2. Edit python312._pth — uncomment the line: import site
3. Download get-pip.py from https://bootstrap.pypa.io/get-pip.py
4. Run: prereqs\python\python.exe get-pip.py
5. Run: prereqs\python\python.exe -m pip install -r BallistiCore_app\backend\requirements.txt
```

The fully installed packages (inside `prereqs/python/Lib/site-packages/`) travel with the installer — no internet needed on the customer's machine.

---

## Build steps (every release)

```bat
REM 1. Build the React frontend
cd BallistiCore_app\frontend
npm run build

REM 2. Open Inno Setup Compiler
REM    File → Open → deploy\installer\ArmsRegister.iss
REM    Build → Compile   (or press F9)

REM Output: dist\ArmsRegister-Setup-1.0.0.exe
```

---

## What the installer does (on the customer's machine)

1. Shows wizard — customer enters: App Name, Company Name, PSIRA #, Reg #, Permit Prefix
2. Installs PostgreSQL 17 silently
3. Copies backend, frontend, nginx, Python, scripts
4. Writes `branding.json` with the customer's details
5. Creates database + user + `.env` file
6. Installs Python packages (from embedded Python — no internet)
7. Runs Alembic migrations (creates all tables)
8. Installs backend as Windows service `ArmsRegister-Backend` (via NSSM)
9. Installs Nginx as Windows service `ArmsRegister-Nginx` (via NSSM)
10. Starts both services
11. Opens `http://localhost` in the browser

**Default login after install:** `admin` / `admin1234` — customer must change on first login.

---

## Updating an existing installation

```bat
REM Stop services
nssm stop ArmsRegister-Backend
nssm stop ArmsRegister-Nginx

REM Replace files (backend + frontend dist)
REM Run migrations
python -m alembic upgrade head

REM Restart
nssm start ArmsRegister-Backend
nssm start ArmsRegister-Nginx
```

Or ship a new installer — the Inno Setup `[Files]` section uses `ignoreversion` so it overwrites safely.

---

## Licensing (for the website)

The `.exe` itself is not licence-locked — this is intentional for simplicity.
Licence enforcement lives at the **download gate** on the BallistiCore website (payment required before download link is issued).

For per-seat enforcement in a future version, a licence key check can be added to the branding wizard page.

---

## Folder layout after install

```
C:\Program Files\ArmsRegister\
├── backend\          ← FastAPI app + branding.json + .env
├── frontend\         ← React dist/ served by Nginx
├── nginx\            ← Nginx binary + conf + logs
├── python\           ← Embedded Python + all packages
├── tools\            ← nssm.exe
├── permits\          ← Generated PDFs (gitignored on dev)
├── backups\          ← pg_dump backups
├── logs\             ← Service logs
└── scripts\          ← backup_db.bat, restore_db.bat, etc.
```
