@echo off
:: BallistiCore — Backend startup script
:: Used by NSSM to launch FastAPI as a Windows service.
:: NSSM should call this script directly, NOT cmd /c this.

cd /d C:\sites\BallistiCore\BallistiCore_app\backend

:: Activate the virtual environment
call .venv\Scripts\activate.bat

:: Start uvicorn with 4 workers
:: --host 127.0.0.1 keeps the API on loopback only (Nginx proxies in)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
