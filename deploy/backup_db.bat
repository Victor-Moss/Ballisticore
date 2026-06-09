@echo off
:: BallistiCore — Daily PostgreSQL backup script
:: Schedule this via Windows Task Scheduler to run daily at e.g. 02:00
::
:: Backups are stored in C:\sites\BallistiCore\backups\
:: Files are named: ballisticore_YYYYMMDD.dump
:: Backups older than 30 days are deleted automatically.

setlocal

set PGPASSWORD=ballisticore_pass
set BACKUP_DIR=C:\sites\BallistiCore\backups
set DB_NAME=ballisticore_db
set DB_USER=ballisticore_user
set PG_DUMP="C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"

:: Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Generate filename with today's date
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
    set DAY=%%a
    set MONTH=%%b
    set YEAR=%%c
)
:: Use wmic for reliable YYYYMMDD format
for /f "skip=1" %%d in ('wmic os get LocalDateTime') do (
    set DT=%%d
    goto :got_date
)
:got_date
set STAMP=%DT:~0,8%
set OUTFILE=%BACKUP_DIR%\ballisticore_%STAMP%.dump

:: Run pg_dump (custom format — compressed, restorable with pg_restore)
%PG_DUMP% -U %DB_USER% -h localhost -p 5432 -Fc -f "%OUTFILE%" %DB_NAME%

if %ERRORLEVEL% == 0 (
    echo [%STAMP%] Backup successful: %OUTFILE%
) else (
    echo [%STAMP%] BACKUP FAILED — check PostgreSQL is running
    exit /b 1
)

:: Delete backups older than 30 days
forfiles /p "%BACKUP_DIR%" /m "*.dump" /d -30 /c "cmd /c del @path" 2>nul

endlocal
