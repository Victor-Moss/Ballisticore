@echo off
rem ============================================================================
rem  BallistiCore — one-time local database setup.
rem  Runs at the end of installation (and is safe to re-run: it no-ops if the
rem  data directory already exists). Everything it creates lives under the
rem  install folder, so all data stays on this machine.
rem ============================================================================
setlocal
call "%~dp0_env.bat"

if exist "%PGDATA%\PG_VERSION" (
  echo Database already initialised - skipping.
  endlocal & exit /b 0
)

if not exist "%LOGS%"   mkdir "%LOGS%"
if not exist "%CONFIG%" mkdir "%CONFIG%"
if not exist "%PERMITS%" mkdir "%PERMITS%"
set "SETUPLOG=%LOGS%\setup.log"
echo [%date% %time%] Starting database setup > "%SETUPLOG%"

rem --- 1) Generate secrets (hex only) -----------------------------------------
rem Write each to a temp file and read it back with set /p. We avoid `for /f`
rem here on purpose: the parentheses in the Python (token_hex(16), print(...))
rem would otherwise close the for-loop's own ( ... ) group and break parsing.
set "STMP=%CONFIG%\_secret.tmp"
"%PY%" -c "import secrets;print(secrets.token_hex(16))" > "%STMP%"
set /p PGPASS=<"%STMP%"
"%PY%" -c "import secrets;print(secrets.token_hex(16))" > "%STMP%"
set /p APPPASS=<"%STMP%"
"%PY%" -c "import secrets;print(secrets.token_hex(32))" > "%STMP%"
set /p SECRET=<"%STMP%"
del "%STMP%" 2>nul

if not defined PGPASS  ( echo ERROR: could not generate secrets - is Python at "%PY%"? & endlocal & exit /b 1 )
if not defined APPPASS ( echo ERROR: could not generate secrets. & endlocal & exit /b 1 )
if not defined SECRET  ( echo ERROR: could not generate secrets. & endlocal & exit /b 1 )

rem --- 2) initdb (superuser 'postgres', password from a temp pwfile) ----------
> "%CONFIG%\_pwfile.txt" echo %PGPASS%
echo Initialising PostgreSQL data directory... >> "%SETUPLOG%"
"%PGBIN%\initdb.exe" -D "%PGDATA%" -U %PGSUPER% --auth-host=scram-sha-256 --auth-local=scram-sha-256 --pwfile="%CONFIG%\_pwfile.txt" -E UTF8 >> "%SETUPLOG%" 2>&1
del "%CONFIG%\_pwfile.txt"
if not exist "%PGDATA%\PG_VERSION" (
  echo ERROR: initdb failed. See "%SETUPLOG%".
  endlocal & exit /b 1
)

rem --- 3) Bind to localhost on our port --------------------------------------
>> "%PGDATA%\postgresql.conf" echo.
>> "%PGDATA%\postgresql.conf" echo # BallistiCore local instance
>> "%PGDATA%\postgresql.conf" echo listen_addresses = 'localhost'
>> "%PGDATA%\postgresql.conf" echo port = %PGPORT%

rem --- 4) Start the server (temporarily, just for setup) ----------------------
rem IMPORTANT: redirect pg_ctl start to its OWN file, not setup.log. The launched
rem postmaster inherits this command's stdout handle for its whole lifetime; if
rem that handle were setup.log, every later ">> setup.log" step would fail with a
rem sharing violation and cmd would silently skip those commands.
echo Starting database... >> "%SETUPLOG%"
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -l "%LOGS%\postgres.log" -w start > "%LOGS%\pg_start.log" 2>&1

rem --- 5) Create the application role and database ----------------------------
set "PGPASSWORD=%PGPASS%"
"%PGBIN%\psql.exe" -h localhost -p %PGPORT% -U %PGSUPER% -d postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE %DBUSER% LOGIN PASSWORD '%APPPASS%';" >> "%SETUPLOG%" 2>&1
"%PGBIN%\psql.exe" -h localhost -p %PGPORT% -U %PGSUPER% -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE %DBNAME% OWNER %DBUSER% ENCODING 'UTF8' TEMPLATE template0;" >> "%SETUPLOG%" 2>&1
set "PGPASSWORD="

rem --- 6) Write the backend .env --------------------------------------------
set "ENVFILE=%BACKEND%\.env"
>  "%ENVFILE%" echo DATABASE_URL=postgresql+psycopg://%DBUSER%:%APPPASS%@localhost:%PGPORT%/%DBNAME%
>> "%ENVFILE%" echo SECRET_KEY=%SECRET%
>> "%ENVFILE%" echo ALGORITHM=HS256
>> "%ENVFILE%" echo ACCESS_TOKEN_EXPIRE_MINUTES=480
>> "%ENVFILE%" echo ENVIRONMENT=production
>> "%ENVFILE%" echo CORS_ORIGINS=http://localhost:%APP_PORT%
>> "%ENVFILE%" echo PDF_STORAGE_PATH=%PERMITS%\
>> "%ENVFILE%" echo FRONTEND_DIST=%FRONTEND_DIST%
>> "%ENVFILE%" echo.
>> "%ENVFILE%" echo # Twilio WhatsApp (outbound only). Leave blank to disable sending.
>> "%ENVFILE%" echo TWILIO_ACCOUNT_SID=
>> "%ENVFILE%" echo TWILIO_AUTH_TOKEN=
>> "%ENVFILE%" echo TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
>> "%ENVFILE%" echo # Public URL Twilio can fetch permit PDFs from (optional). Blank = text-only.
>> "%ENVFILE%" echo PUBLIC_BASE_URL=

rem --- 7) Create tables (Alembic migrations) ---------------------------------
echo Creating database tables... >> "%SETUPLOG%"
pushd "%BACKEND%"
"%PY%" -m alembic upgrade head >> "%SETUPLOG%" 2>&1
popd

rem --- 8) Stop the server; the launcher starts it on demand ------------------
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -w stop -m fast >> "%SETUPLOG%" 2>&1

echo [%date% %time%] Setup complete. >> "%SETUPLOG%"
echo Database setup complete.
endlocal & exit /b 0
