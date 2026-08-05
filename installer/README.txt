============================================================
 BallistiCore — Firearms Register Management
 Self-hosted edition — Setup & Usage
============================================================

WHAT THIS IS
------------
BallistiCore runs entirely on this Windows PC. It bundles everything it
needs (its database, web server and application), so there is nothing else
to install and no internet connection is required to use it. All of your
data stays on this machine.


INSTALLING
----------
1. Double-click  BallistiCore-Setup-1.7.0.exe
2. Choose where to install it (the default is fine).
3. Enter your company name and permit prefix when asked.
4. Click Install and wait for it to finish (the first-time database
   setup can take a minute).
5. Leave "Start BallistiCore now" ticked and click Finish.


STARTING THE APP
----------------
- Use the BallistiCore desktop shortcut (or Start-menu entry).
- A small window appears while it starts, then your web browser opens
  automatically at:   http://localhost:8000
- The first login is:
       Username:  admin
       Password:  admin1234
  >>> Change this password immediately in Admin > Users. <<<

You can close the small black window once the app has opened — the app
keeps running in the background.


STOPPING THE APP
----------------
- Use the "Stop BallistiCore" shortcut in the Start menu, or simply
  restart/shut down the PC.


USING IT FROM OTHER DEVICES ON THE SAME NETWORK
-----------------------------------------------
Other computers, tablets and phones on the same office network (wired or
Wi-Fi) can use BallistiCore out of the box - no extra setup needed. The
installer already opened the required Windows Firewall port for you.
  1. Find this PC's network address (run  ipconfig  -> IPv4 Address),
     e.g. 192.168.1.20. The Finish screen of the in-app setup wizard also
     shows this address.
  2. On the other device, open a web browser and go to:
        http://YOUR-PC-IP:8000       (e.g. http://192.168.1.20:8000)
  3. Sign in as usual. Everyone shares the same data on this PC, which
     must be switched on and running BallistiCore.

If a device can't connect, confirm both are on the same network and that
the "BallistiCore" inbound firewall rule is present (it is added during
installation; you can re-add it by running  scripts\firewall.bat  as
administrator).


WHATSAPP PERMIT DELIVERY (optional)
-----------------------------------
BallistiCore can send permit notifications to guards over WhatsApp using
Twilio. This is OUTBOUND ONLY and is OFF until you add credentials.
To enable it, edit  <install folder>\backend\.env :
        TWILIO_ACCOUNT_SID=your-sid
        TWILIO_AUTH_TOKEN=your-token
        TWILIO_WHATSAPP_FROM=whatsapp:+<your-twilio-number>
Then use "Stop BallistiCore" and start it again.
(Sending the PDF as an attachment additionally requires a public URL in
PUBLIC_BASE_URL; without it, guards receive a text notification.)


ELECTRONIC SIGNATURES ON ISSUE & RETURN
---------------------------------------
When a firearm is issued AND when it is returned, BallistiCore captures two
electronic signatures - the staff member handling it and the guard - by each
entering their own password. Both are stored against the permit and printed
on the permit PDF, as required for Firearms Control Act / PSIRA records.

  - The staff member's signature is ALWAYS required; the action cannot be
    completed without it.
  - The guard's signature is required as soon as that guard has a sign-in
    account. A guard who does not yet have an account can still be issued to
    and can still return a firearm - their side is recorded as "unsigned" and
    the screen shows an amber notice.

To ensure every issue and return is fully dual-signed, give each guard a
sign-in account (Guards > select the guard > set up sign-in). Until then the
unsigned notice is your reminder that a guard account is still outstanding.


BACKING UP YOUR DATA
--------------------
Everything lives inside the install folder. The important parts are:
   pgdata\          - the database (all guards, firearms, permits, history)
   backend\permits\ - generated permit PDFs
   backend\.env     - your configuration (database password, keys)
To back up: stop BallistiCore, then copy the whole install folder to a
safe location (e.g. an external drive).


TROUBLESHOOTING
---------------
- "It won't open in the browser": wait a few seconds and re-run the
  BallistiCore shortcut; the first start is the slowest.
- Check the log files in  <install folder>\logs\  :
      setup.log     - first-run database setup
      postgres.log  - database
      (the server window shows backend messages)
- Port 8000 already in use? Change APP_PORT in scripts\_env.bat and
  CORS_ORIGINS in backend\.env to match.


UNINSTALLING
------------
Use "Uninstall BallistiCore" from the Start menu (or Windows
Settings > Apps). Your data folders (pgdata, permits, logs, config) are
left in place so nothing is lost by accident — delete the install folder
manually if you also want to remove the data.

============================================================
