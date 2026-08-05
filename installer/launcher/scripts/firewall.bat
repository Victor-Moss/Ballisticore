@echo off
rem ============================================================================
rem  BallistiCore - Windows Firewall inbound rule for the app port.
rem  Lets other devices on the same LAN/Wi-Fi reach the app at
rem  http://<this-PC-IP>:<port>. Changing firewall rules needs administrator
rem  rights, so the installer runs this elevated (one UAC prompt). If the user
rem  declines, the app still works locally - only off-machine access is blocked.
rem
rem  Usage:  firewall.bat add     (default) - create/refresh the inbound rule
rem          firewall.bat remove            - delete the rule (used on uninstall)
rem ============================================================================
setlocal
call "%~dp0_env.bat"
set "RULE=BallistiCore"

if /i "%~1"=="remove" (
  netsh advfirewall firewall delete rule name="%RULE%" >nul 2>&1
  exit /b 0
)

rem Add (default). Delete any existing rule of the same name first so repeated
rem installs/upgrades don't stack duplicate rules, then add a fresh inbound TCP
rem allow scoped to just our port. profile=any covers Private/Domain/Public so
rem it works whether Windows classified this Wi-Fi as Private or Public.
netsh advfirewall firewall delete rule name="%RULE%" >nul 2>&1
netsh advfirewall firewall add rule name="%RULE%" dir=in action=allow protocol=TCP localport=%APP_PORT% profile=any
exit /b %errorlevel%
