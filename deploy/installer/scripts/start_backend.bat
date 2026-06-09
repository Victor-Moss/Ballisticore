@echo off
REM Manually start the ArmsRegister backend and web server services.
net start ArmsRegister-Backend
net start ArmsRegister-Nginx
echo Services started.
pause
