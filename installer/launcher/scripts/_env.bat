@echo off
rem ============================================================================
rem  BallistiCore — shared environment for all launcher scripts.
rem  Resolves the install root from this file's location, so the whole folder
rem  can live anywhere (C:\BallistiCore, a USB drive, etc.) and still work.
rem ============================================================================

rem ROOT = parent of this \scripts folder
for %%I in ("%~dp0..") do set "ROOT=%%~fI"

set "PY=%ROOT%\python\python.exe"
set "PGBIN=%ROOT%\pgsql\bin"
set "PGDATA=%ROOT%\pgdata"
set "BACKEND=%ROOT%\backend"
set "FRONTEND_DIST=%ROOT%\frontend"
set "LOGS=%ROOT%\logs"
set "CONFIG=%ROOT%\config"
rem The PDF generator writes to <backend>\permits, so keep them together.
set "PERMITS=%ROOT%\backend\permits"

rem Network — loopback only; nothing is exposed off this machine by default.
set "APP_HOST=127.0.0.1"
set "APP_PORT=8000"
rem 5433 (not the default 5432) so the bundled DB won't clash with any
rem PostgreSQL the client may already have installed on this PC.
set "PGPORT=5433"

rem Database identities
set "PGSUPER=postgres"
set "DBNAME=ballisticore_db"
set "DBUSER=ballisticore_user"
