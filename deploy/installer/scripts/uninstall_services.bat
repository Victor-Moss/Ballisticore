@echo off
REM Called by Inno Setup uninstaller.
SET APP_DIR=%~1

"%APP_DIR%\tools\nssm.exe" stop ArmsRegister-Backend 2>nul
"%APP_DIR%\tools\nssm.exe" remove ArmsRegister-Backend confirm 2>nul
"%APP_DIR%\tools\nssm.exe" stop ArmsRegister-Nginx 2>nul
"%APP_DIR%\tools\nssm.exe" remove ArmsRegister-Nginx confirm 2>nul

echo Services removed.
