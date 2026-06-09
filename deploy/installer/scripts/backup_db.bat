@echo off
REM Creates a timestamped pg_dump backup of the ArmsRegister database.

SET APP_DIR=%~dp0..
SET PGBIN=C:\Program Files\PostgreSQL\17\bin
SET DB_NAME=armsregister_db
SET DB_USER=armsregister_user
SET TIMESTAMP=%DATE:~-4,4%%DATE:~-7,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET OUTFILE=%APP_DIR%\backups\%DB_NAME%_%TIMESTAMP%.dump

"%PGBIN%\pg_dump.exe" -U %DB_USER% -Fc -f "%OUTFILE%" %DB_NAME%

if %ERRORLEVEL% == 0 (
    echo Backup saved to: %OUTFILE%
) else (
    echo Backup failed. Check that PostgreSQL is running.
)
pause
