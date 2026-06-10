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
1. Double-click  BallistiCore-Setup-1.3.0.exe
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


USING IT FROM OTHER DEVICES ON THE SAME NETWORK (optional)
----------------------------------------------------------
By default the app is reachable only from this PC. To allow other
computers or phones on the same office network to use it:
  1. Find this PC's network address (run  ipconfig  -> IPv4 Address).
  2. Edit  <install folder>\scripts\_env.bat  and change
        set "APP_HOST=127.0.0.1"
     to
        set "APP_HOST=0.0.0.0"
  3. Add the new address to CORS in  <install folder>\backend\.env :
        CORS_ORIGINS=http://localhost:8000,http://YOUR-PC-IP:8000
  4. Allow port 8000 through Windows Firewall if prompted.
  5. Other devices then open:  http://YOUR-PC-IP:8000


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
