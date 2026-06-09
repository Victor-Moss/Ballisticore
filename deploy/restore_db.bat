@echo off
:: BallistiCore — Database restore script
:: Usage: restore_db.bat C:\sites\BallistiCore\backups\ballisticore_20260330.dump
::
:: WARNING: This DROPS and recreates the database. All current data will be lost.

if "%~1"=="" (
    echo Usage: restore_db.bat ^<path-to-dump-file^>
    exit /b 1
)

set DUMP_FILE=%~1
set PGPASSWORD=ballisticore_pass
set DB_NAME=ballisticore_db
set DB_USER=ballisticore_user
set PG_RESTORE="C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"
set PSQL="C:\Program Files\PostgreSQL\17\bin\psql.exe"

echo.
echo WARNING: This will DROP and recreate %DB_NAME%
echo Restore file: %DUMP_FILE%
echo.
set /p CONFIRM=Type YES to continue:

if /i not "%CONFIRM%"=="YES" (
    echo Cancelled.
    exit /b 0
)

echo Dropping and recreating database...
%PSQL% -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='%DB_NAME%';"
%PSQL% -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"
%PSQL% -U postgres -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"
%PSQL% -U postgres -d %DB_NAME% -c "GRANT ALL ON SCHEMA public TO %DB_USER%;"

echo Restoring from backup...
%PG_RESTORE% -U %DB_USER% -h localhost -d %DB_NAME% "%DUMP_FILE%"

if %ERRORLEVEL% == 0 (
    echo Restore complete.
) else (
    echo Restore encountered errors — check output above.
)
