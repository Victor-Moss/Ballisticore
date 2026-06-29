@echo off
rem ============================================================================
rem  BallistiCore - start everything and open the app.
rem  Idempotent: if it's already running, it just opens the browser.
rem ============================================================================
setlocal
call "%~dp0_env.bat"
if not exist "%LOGS%" mkdir "%LOGS%"

rem --- Already running? Just open the browser. -------------------------------
powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient;$c.Connect('127.0.0.1',%APP_PORT%);$c.Close();exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 (
  echo BallistiCore is already running.
  start "" "http://localhost:%APP_PORT%"
  endlocal & exit /b 0
)

rem --- First run? Set up the local database. ---------------------------------
if not exist "%PGDATA%\PG_VERSION" call "%~dp0init_db.bat"

rem --- Start PostgreSQL if it isn't up. --------------------------------------
"%PGBIN%\pg_isready.exe" -h localhost -p %PGPORT% -q
if not %errorlevel%==0 (
  echo Starting database...
  "%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -l "%LOGS%\postgres.log" -w start
)

rem --- Apply any pending database migrations (idempotent; no-op when current).-
rem  Runs on EVERY launch, not just first run, so upgrading the app over an
rem  existing install always brings the schema up to date before the backend
rem  serves requests. alembic upgrade head is a fast no-op when already current;
rem  without this, a release that adds columns would start against the old
rem  schema and every query touching the new column would fail.
echo Applying database updates...
pushd "%BACKEND%"
"%PY%" -m alembic upgrade head >> "%LOGS%\migrate.log" 2>&1
if not %errorlevel%==0 echo   Note: a database update step reported an error - see "%LOGS%\migrate.log".
popd

rem --- Start the backend (serves API + UI) in a minimised window. ------------
echo Starting BallistiCore...
pushd "%BACKEND%"
start "BallistiCore Server" /MIN "%PY%" -m uvicorn app.main:app --host %APP_HOST% --port %APP_PORT%
popd

rem --- Wait for health, then open the browser. -------------------------------
set /a tries=0
:waitloop
powershell -NoProfile -Command "try{Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%APP_PORT%/health ^| Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 goto ready
set /a tries+=1
if %tries% GEQ 40 goto ready
rem ~1s sleep via ping (timeout.exe fails when stdin is redirected / non-interactive)
ping -n 2 127.0.0.1 >nul
goto waitloop

:ready
start "" "http://localhost:%APP_PORT%"
echo.
echo BallistiCore is running at http://localhost:%APP_PORT%
echo You can close this window; the app keeps running in the background.
echo Use "Stop BallistiCore" to shut it down.
endlocal & exit /b 0
