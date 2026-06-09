<#
  build_payload.ps1 — stage everything BallistiCore.iss needs into .\payload\

  Run this on a Windows build machine BEFORE compiling the installer.

  It will:
    1. Verify you have supplied bundled Python and PostgreSQL (see BUILD.md).
    2. Build the React frontend and copy dist\ -> payload\frontend\
    3. Copy the FastAPI backend           -> payload\backend\
    4. pip-install the backend's runtime deps into the bundled Python.

  After it succeeds, open BallistiCore.iss in Inno Setup and press Compile (F9).

  Usage:   powershell -ExecutionPolicy Bypass -File build_payload.ps1
#>

$ErrorActionPreference = 'Stop'
$Here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo     = Split-Path -Parent $Here
$AppRoot  = Join-Path $Repo 'BallistiCore_app'
$Payload  = Join-Path $Here 'payload'

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "`nERROR: $m" -ForegroundColor Red; exit 1 }

# ── 0. Preconditions: builder-supplied binaries ────────────────────────────
$PyExe = Join-Path $Payload 'python\python.exe'
$PgCtl = Join-Path $Payload 'pgsql\bin\pg_ctl.exe'

if (-not (Test-Path $PyExe)) {
  Fail @"
Bundled Python not found at payload\python\python.exe

Provide a relocatable CPython 3.12 (x64) there. Recommended:
  python-build-standalone (https://github.com/astral-sh/python-build-standalone)
  Download the 'cpython-3.12.*-x86_64-pc-windows-msvc-install_only' archive,
  extract it, and copy its contents so that payload\python\python.exe exists.
See BUILD.md for details.
"@
}
if (-not (Test-Path $PgCtl)) {
  Fail @"
Bundled PostgreSQL not found at payload\pgsql\bin\pg_ctl.exe

Download the PostgreSQL 16/17 'Windows x86-64 binaries' ZIP (the portable
zip, not the installer) from https://www.enterprisedb.com/download-postgresql-binaries
Extract it and copy the inner 'pgsql' folder to payload\pgsql so that
payload\pgsql\bin\pg_ctl.exe exists. See BUILD.md.
"@
}

# ── 1. Build the frontend ──────────────────────────────────────────────────
Step 'Building React frontend (npm run build)'
$Frontend = Join-Path $AppRoot 'frontend'
Push-Location $Frontend
try {
  if (-not (Test-Path (Join-Path $Frontend 'node_modules'))) {
    Write-Host 'Installing npm dependencies...'
    npm install
    if ($LASTEXITCODE -ne 0) { Fail 'npm install failed.' }
  }
  npm run build
  if ($LASTEXITCODE -ne 0) { Fail 'npm run build failed.' }
} finally { Pop-Location }

Step 'Staging frontend -> payload\frontend'
$PFrontend = Join-Path $Payload 'frontend'
if (Test-Path $PFrontend) { Remove-Item $PFrontend -Recurse -Force }
New-Item -ItemType Directory -Path $PFrontend | Out-Null
Copy-Item (Join-Path $Frontend 'dist\*') $PFrontend -Recurse -Force

# ── 2. Stage the backend (exclude dev cruft + local secrets) ───────────────
Step 'Staging backend -> payload\backend'
$Backend  = Join-Path $AppRoot 'backend'
$PBackend = Join-Path $Payload 'backend'
if (Test-Path $PBackend) { Remove-Item $PBackend -Recurse -Force }
# robocopy exit codes 0-7 are success; treat 8+ as failure.
robocopy $Backend $PBackend /E /NFL /NDL /NJH /NJS /NP `
  /XD '.venv' '__pycache__' '.pytest_cache' 'tests' 'permits' `
  /XF '.env' '*.pyc' | Out-Null
if ($LASTEXITCODE -ge 8) { Fail "robocopy failed (code $LASTEXITCODE)." }
$global:LASTEXITCODE = 0

# ── 3. Install backend runtime deps into the bundled Python ────────────────
Step 'Installing backend runtime dependencies into bundled Python'
& $PyExe -m ensurepip --upgrade 2>$null
& $PyExe -m pip install --upgrade pip --no-warn-script-location
& $PyExe -m pip install --no-warn-script-location -r (Join-Path $Here 'requirements-runtime.txt')
if ($LASTEXITCODE -ne 0) { Fail 'pip install of runtime dependencies failed.' }

# Sanity check: can the bundled Python import the app and launch tooling?
& $PyExe -c "import fastapi, uvicorn, alembic, psycopg, twilio, reportlab; print('deps OK')"
if ($LASTEXITCODE -ne 0) { Fail 'Bundled Python could not import the required packages.' }

Step 'Payload staged successfully.'
Write-Host "  payload\python    (Python + dependencies)"
Write-Host "  payload\pgsql     (PostgreSQL binaries)"
Write-Host "  payload\backend   (FastAPI app)"
Write-Host "  payload\frontend  (built React UI)"
Write-Host "`nNext: open BallistiCore.iss in Inno Setup and press Compile (F9)." -ForegroundColor Green
