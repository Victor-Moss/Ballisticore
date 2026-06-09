@echo off
REM Restores a pg_dump backup file into the ArmsRegister database.
REM Usage: restore_db.bat <path-to-dump-file>

SET PGBIN=C:\Program Files\PostgreSQL\17\bin
SET DB_NAME=armsregister_db
SET DB_USER=armsregister_user

IF "%~1"=="" (
    echo Usage: restore_db.bat ^<path-to-dump-file^>
    pause
    exit /b 1
)

SET DUMPFILE=%~1

echo WARNING: This will overwrite all data in %DB_NAME%.
set /p CONFIRM=Type YES to continue:
if /i NOT "%CONFIRM%"=="YES" (
    echo Cancelled.
    pause
    exit /b 0
)

"%PGBIN%\pg_restore.exe" -U %DB_USER% -d %DB_NAME% --clean --if-exists "%DUMPFILE%"

if %ERRORLEVEL% == 0 (
    echo Restore complete.
) else (
    echo Restore failed. Check PostgreSQL logs.
)
pause
