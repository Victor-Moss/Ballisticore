@echo off
rem ============================================================================
rem  BallistiCore — stop the backend and the database.
rem ============================================================================
setlocal
call "%~dp0_env.bat"

echo Stopping BallistiCore server...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*uvicorn app.main:app*' -and $_.CommandLine -like '*%APP_PORT%*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo Stopping database...
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -w stop -m fast >nul 2>&1

echo BallistiCore stopped.
ping -n 3 127.0.0.1 >nul
endlocal & exit /b 0
