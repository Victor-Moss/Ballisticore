# BallistiCore — LAN Deployment Guide

**Target:** Single Windows server on the local network.
**Access:** Any browser on the LAN at `http://<server-ip>` — no internet needed.

---

## Architecture

```
[LAN workstations] ── browser :80 ──▶ Nginx (Windows)
                                           │
                              ┌────────────┴────────────┐
                     React dist/ (static)        /api/ proxy
                                                      │
                                              FastAPI :8000
                                              (uvicorn, loopback only)
                                                      │
                                              PostgreSQL :5432
```

---

## Step 1 — Find the Server's LAN IP

On the Windows server, open Command Prompt and run:
```cmd
ipconfig
```
Note the **IPv4 Address** under your LAN adapter (e.g. `192.168.1.100`).
This is the address users will type in their browsers.

---

## Step 2 — Production .env

Copy the template and fill it in:
```
deploy\env.production.template  →  BallistiCore_app\backend\.env
```

Key fields to update:
- `SECRET_KEY` — generate with: `.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"`
- `CORS_ORIGINS` — set to the server's LAN IP: `http://192.168.1.100`
- `PDF_STORAGE_PATH` — `C:\sites\BallistiCore\permits\`
- Create the permits folder: `mkdir C:\sites\BallistiCore\permits`

---

## Step 3 — Build the Frontend

Open a terminal in `BallistiCore_app\frontend\` and run:
```cmd
npm run build
```

Output goes to `frontend\dist\` — this is what Nginx serves.
Re-run this command after every frontend code change.

---

## Step 4 — Install Nginx for Windows

1. Download **Nginx for Windows** from https://nginx.org/en/download.html
   Choose the latest **stable** `.zip` (e.g. `nginx-1.26.x.zip`)

2. Extract to `C:\nginx\`

3. Replace `C:\nginx\conf\nginx.conf` with the file at `deploy\nginx.conf`

4. Edit the `nginx.conf` — find this line and set your server's LAN IP:
   ```nginx
   # server_name 192.168.1.100;
   ```
   Uncomment it and replace with your actual IP.

5. Test the config:
   ```cmd
   C:\nginx\nginx.exe -t
   ```

6. Start Nginx:
   ```cmd
   C:\nginx\nginx.exe
   ```

7. To reload config without stopping (after changes):
   ```cmd
   C:\nginx\nginx.exe -s reload
   ```

8. To stop Nginx:
   ```cmd
   C:\nginx\nginx.exe -s stop
   ```

---

## Step 5 — Run FastAPI as a Windows Service (NSSM)

NSSM (Non-Sucking Service Manager) wraps any executable as a Windows service that starts automatically on boot.

### Install NSSM
1. Download from https://nssm.cc/download
2. Extract and copy `nssm.exe` (64-bit) to `C:\Windows\System32\` (or add its folder to PATH)

### Create the BallistiCore service
Open **Command Prompt as Administrator** and run:

```cmd
nssm install BallistiCore
```

In the NSSM GUI that appears, fill in:

| Field | Value |
|-------|-------|
| **Application → Path** | `C:\sites\BallistiCore\BallistiCore_app\backend\.venv\Scripts\uvicorn.exe` |
| **Application → Startup directory** | `C:\sites\BallistiCore\BallistiCore_app\backend` |
| **Application → Arguments** | `app.main:app --host 127.0.0.1 --port 8000 --workers 4` |
| **Details → Display name** | `BallistiCore API` |
| **Details → Startup type** | `Automatic` |
| **Log on → Log on as** | `Local System` |

Click **Install service**.

### Start the service
```cmd
nssm start BallistiCore
```

### Check it's running
```cmd
nssm status BallistiCore
```
Then visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

### Other service commands
```cmd
nssm stop BallistiCore
nssm restart BallistiCore
nssm remove BallistiCore confirm    # uninstall the service
```

---

## Step 6 — Run Nginx as a Windows Service (NSSM)

```cmd
nssm install Nginx
```

| Field | Value |
|-------|-------|
| **Path** | `C:\nginx\nginx.exe` |
| **Startup directory** | `C:\nginx` |
| **Display name** | `Nginx` |
| **Startup type** | `Automatic` |

```cmd
nssm start Nginx
```

---

## Step 7 — Windows Firewall

Allow inbound HTTP traffic on port 80:

```cmd
netsh advfirewall firewall add rule name="BallistiCore HTTP" protocol=TCP dir=in localport=80 action=allow
```

Port 8000 does **not** need to be opened — Nginx proxies to it internally on loopback.

---

## Step 8 — Set Up Daily Database Backup

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Basic Task**
3. Name: `BallistiCore DB Backup`
4. Trigger: **Daily** at `02:00`
5. Action: **Start a program**
   - Program: `C:\sites\BallistiCore\deploy\backup_db.bat`
6. Finish

Edit `deploy\backup_db.bat` and update the `PGPASSWORD` line with your actual DB password.

Backups are stored in `C:\sites\BallistiCore\backups\` and auto-deleted after 30 days.

### To restore from backup
```cmd
deploy\restore_db.bat C:\sites\BallistiCore\backups\ballisticore_20260330.dump
```

---

## Step 9 — Verify Everything Works

1. Open a browser **on a different machine** on the LAN
2. Navigate to `http://192.168.1.100` (use your server's actual IP)
3. You should see the BallistiCore login page
4. Log in with `admin` / `admin1234`
5. **Change the admin password immediately** via Admin → User Management

Check all critical flows:
- [ ] Login works
- [ ] Create a guard
- [ ] Add a firearm
- [ ] Set guard permission for firearm
- [ ] Issue firearm → permit PDF generated
- [ ] Download permit PDF
- [ ] Return firearm
- [ ] Export history Excel

---

## Step 10 — Post-Deployment Security Checklist

- [ ] Change default `admin` password (`admin1234` → strong password)
- [ ] Generate a proper `SECRET_KEY` in `.env` (not the placeholder)
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Confirm `PDF_STORAGE_PATH` is an absolute path and the folder exists
- [ ] Confirm PostgreSQL only accepts local connections (default on Windows install)
- [ ] Confirm port 8000 is NOT open in Windows Firewall (only 80 should be)
- [ ] Test backup script runs successfully and creates a `.dump` file
- [ ] Test restore process on a copy before you need it

---

## Updating the System

### After backend code changes:
```cmd
nssm restart BallistiCore
```

### After frontend code changes:
```cmd
cd C:\sites\BallistiCore\BallistiCore_app\frontend
npm run build
C:\nginx\nginx.exe -s reload
```

### After database model changes:
```cmd
cd C:\sites\BallistiCore\BallistiCore_app\backend
.venv\Scripts\activate
alembic upgrade head
nssm restart BallistiCore
```

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| Can't reach site from other machine | Windows Firewall — port 80 open? |
| Site loads but API calls fail (401/404) | Nginx running? `nssm status Nginx` |
| API returns 500 errors | NSSM logs: `C:\ProgramData\nssm\BallistiCore\` |
| PDF download fails | `PDF_STORAGE_PATH` in `.env` — folder exists and writable? |
| DB connection error on startup | PostgreSQL service running? Password correct in `.env`? |
| "Could not connect to server" | Check `nssm status BallistiCore` and review logs |

### View service logs (NSSM)
By default NSSM writes stdout/stderr to:
- `C:\ProgramData\nssm\BallistiCore\BallistiCore.exe-stdout.log`
- `C:\ProgramData\nssm\BallistiCore\BallistiCore.exe-stderr.log`

Or configure log files in NSSM GUI: **I/O tab → Output / Error**.
