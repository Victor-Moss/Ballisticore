; ============================================================
;  ArmsRegister — Inno Setup installer script
;  Builds a single .exe that installs everything on Windows.
;
;  Prerequisites bundled in deploy/installer/prereqs/:
;    postgresql-17-windows-x64.exe   (PostgreSQL 17 silent installer)
;    nssm/nssm.exe                   (NSSM 2.24, win64 build)
;    nginx/                          (Nginx 1.26 extracted folder)
;    python/                         (Embedded Python 3.12 + site-packages)
;
;  Build steps:
;    1. npm run build   (inside BallistiCore_app/frontend)
;    2. Compile this .iss in Inno Setup Compiler  (F9)
;    3. Distribute dist\ArmsRegister-Setup-1.0.0.exe
; ============================================================

#define AppName    "ArmsRegister"
#define AppVersion "1.0.0"
#define AppPublisher "BallistiCore"
#define AppURL     "https://ballisticore.co.za"
#define InstallDir "{commonpf64}\ArmsRegister"

[Setup]
AppId={{B8F4C2A1-7D3E-4F6B-9A2C-1E5D8F3B7C4A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={#InstallDir}
DefaultGroupName={#AppName}
OutputDir=..\..\dist
OutputBaseFilename=ArmsRegister-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=assets\icon.ico
WizardImageFile=assets\wizard-banner.bmp
WizardSmallImageFile=assets\wizard-small.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Dirs]
Name: "{app}"
Name: "{app}\backend"
Name: "{app}\frontend"
Name: "{app}\nginx"
Name: "{app}\nginx\logs"
Name: "{app}\logs"
Name: "{app}\backups"
Name: "{app}\permits"
Name: "{app}\tools"
Name: "{app}\scripts"

[Files]
; ── PostgreSQL installer (extracted to temp, deleted after) ───────────────────
Source: "prereqs\postgresql-17-windows-x64.exe"; DestDir: "{tmp}"; \
  Flags: deleteafterinstall

; ── Backend ──────────────────────────────────────────────────────────────────
Source: "..\..\BallistiCore_app\backend\*"; DestDir: "{app}\backend"; \
  Flags: recursesubdirs ignoreversion; \
  Excludes: ".venv,__pycache__,*.pyc,tests,.env,permits"

; ── Frontend (built dist/) ───────────────────────────────────────────────────
Source: "..\..\BallistiCore_app\frontend\dist\*"; DestDir: "{app}\frontend"; \
  Flags: recursesubdirs ignoreversion

; ── Nginx ────────────────────────────────────────────────────────────────────
Source: "prereqs\nginx\*"; DestDir: "{app}\nginx"; \
  Flags: recursesubdirs ignoreversion
; nginx.conf goes to conf/ with FRONTEND_PATH placeholder (patched in [Code])
Source: "nginx.conf.template"; DestDir: "{app}\nginx\conf"; \
  DestName: "nginx.conf"; Flags: ignoreversion

; ── NSSM ─────────────────────────────────────────────────────────────────────
Source: "prereqs\nssm\nssm.exe"; DestDir: "{app}\tools"; Flags: ignoreversion

; ── Python embedded ──────────────────────────────────────────────────────────
Source: "prereqs\python\*"; DestDir: "{app}\python"; \
  Flags: recursesubdirs ignoreversion

; ── Scripts ──────────────────────────────────────────────────────────────────
Source: "scripts\setup_db.bat";         DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\start_backend.bat";    DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\backup_db.bat";        DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\restore_db.bat";       DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\uninstall_services.bat"; DestDir: "{app}\scripts"; Flags: ignoreversion

; ── App launcher shortcut ────────────────────────────────────────────────────
Source: "open_app.bat"; DestDir: "{app}"; Flags: ignoreversion

; ── Branding template (only if no branding.json exists yet) ─────────────────
Source: "..\..\BallistiCore_app\backend\branding.json"; \
  DestDir: "{app}\backend"; Flags: ignoreversion onlyifdoesntexist

; ── Icons ────────────────────────────────────────────────────────────────────
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\open_app.bat"; \
  IconFilename: "{app}\icon.ico"; Comment: "Open {#AppName} in your browser"
Name: "{group}\Backup Database";  Filename: "{app}\scripts\backup_db.bat"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\open_app.bat"; \
  IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
; 1. Install PostgreSQL silently
Filename: "{tmp}\postgresql-17-windows-x64.exe"; \
  Parameters: "--mode unattended --superpassword postgres --serverport 5432"; \
  StatusMsg: "Installing PostgreSQL 17…"; Flags: waituntilterminated

; 2. Set up database, user, and .env file
Filename: "{app}\scripts\setup_db.bat"; \
  Parameters: """{app}"""; \
  StatusMsg: "Configuring database…"; \
  Flags: waituntilterminated runhidden

; 3. Install Python packages into embedded Python
Filename: "{app}\python\python.exe"; \
  Parameters: "-m pip install -r ""{app}\backend\requirements.txt"" --quiet"; \
  StatusMsg: "Installing Python packages (this may take a minute)…"; \
  Flags: waituntilterminated runhidden

; 4. Run Alembic migrations
Filename: "{app}\python\python.exe"; \
  Parameters: "-m alembic upgrade head"; \
  WorkingDir: "{app}\backend"; \
  StatusMsg: "Setting up database tables…"; Flags: waituntilterminated runhidden

; 5. Install backend as a Windows service via NSSM
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "install ArmsRegister-Backend ""{app}\python\python.exe"" ""-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2"""; \
  StatusMsg: "Installing backend service…"; Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Backend AppDirectory ""{app}\backend"""; \
  Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Backend AppStdout ""{app}\logs\backend.log"""; \
  Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Backend AppStderr ""{app}\logs\backend-error.log"""; \
  Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Backend Start SERVICE_AUTO_START"; \
  Flags: waituntilterminated runhidden

; 6. Install Nginx as a Windows service via NSSM
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "install ArmsRegister-Nginx ""{app}\nginx\nginx.exe"""; \
  StatusMsg: "Installing web server service…"; Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Nginx AppDirectory ""{app}\nginx"""; \
  Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Nginx AppStdout ""{app}\logs\nginx.log"""; \
  Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; \
  Parameters: "set ArmsRegister-Nginx Start SERVICE_AUTO_START"; \
  Flags: waituntilterminated runhidden

; 7. Start both services
Filename: "{app}\tools\nssm.exe"; Parameters: "start ArmsRegister-Backend"; \
  StatusMsg: "Starting backend service…"; Flags: waituntilterminated runhidden
Filename: "{app}\tools\nssm.exe"; Parameters: "start ArmsRegister-Nginx"; \
  StatusMsg: "Starting web server…"; Flags: waituntilterminated runhidden

; 8. Open the app in the browser (optional post-install step user can click)
Filename: "{app}\open_app.bat"; \
  Description: "Open {#AppName} in your browser now"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\scripts\uninstall_services.bat"; \
  Parameters: """{app}"""; Flags: waituntilterminated runhidden

[Code]
// ── Wizard page: branding fields ─────────────────────────────────────────────
var
  BrandingPage: TInputQueryWizardPage;

procedure InitializeWizard();
begin
  BrandingPage := CreateInputQueryPage(wpSelectDir,
    'Company Branding',
    'Enter your company details.',
    'These details will appear on the login screen, sidebar, and all printed permits.');

  BrandingPage.Add('Application name:', False);
  BrandingPage.Add('Company name:', False);
  BrandingPage.Add('PSIRA number:', False);
  BrandingPage.Add('Company registration number:', False);
  BrandingPage.Add('Permit number prefix (1–4 letters, e.g. AR):', False);

  BrandingPage.Values[0] := 'BallistiCore';
  BrandingPage.Values[1] := '';
  BrandingPage.Values[2] := '';
  BrandingPage.Values[3] := '';
  BrandingPage.Values[4] := 'BC';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Prefix: String;
begin
  Result := True;
  if CurPageID = BrandingPage.ID then
  begin
    if Trim(BrandingPage.Values[0]) = '' then
    begin
      MsgBox('Application name is required.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if Trim(BrandingPage.Values[1]) = '' then
    begin
      MsgBox('Company name is required.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    Prefix := UpperCase(Trim(BrandingPage.Values[4]));
    if (Length(Prefix) < 1) or (Length(Prefix) > 4) then
    begin
      MsgBox('Permit prefix must be 1–4 letters.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    BrandingPage.Values[4] := Prefix;
  end;
end;

// ── Replace FRONTEND_PATH in nginx.conf ──────────────────────────────────────
procedure PatchNginxConf(AppDir: String);
var
  ConfPath: String;
  Lines: TStringList;
  FrontendPath: String;
  I: Integer;
begin
  ConfPath := AppDir + '\nginx\conf\nginx.conf';
  // Nginx requires forward slashes in paths
  FrontendPath := AppDir + '\frontend';
  StringChangeEx(FrontendPath, '\', '/', True);

  Lines := TStringList.Create;
  try
    Lines.LoadFromFile(ConfPath);
    for I := 0 to Lines.Count - 1 do
    begin
      if Pos('FRONTEND_PATH', Lines[I]) > 0 then
        Lines[I] := StringReplace(Lines[I], 'FRONTEND_PATH', FrontendPath, []);
    end;
    Lines.SaveToFile(ConfPath);
  finally
    Lines.Free;
  end;
end;

// ── Write branding.json with installer wizard values ─────────────────────────
procedure WriteBrandingJson(AppDir: String);
var
  Json: TStringList;
  FilePath: String;
begin
  Json := TStringList.Create;
  try
    Json.Add('{');
    Json.Add('  "app_name": "' + BrandingPage.Values[0] + '",');
    Json.Add('  "company_name": "' + BrandingPage.Values[1] + '",');
    Json.Add('  "psira_number": "' + BrandingPage.Values[2] + '",');
    Json.Add('  "company_reg": "' + BrandingPage.Values[3] + '",');
    Json.Add('  "permit_prefix": "' + BrandingPage.Values[4] + '",');
    Json.Add('  "primary_color": "#1d4ed8"');
    Json.Add('}');
    FilePath := AppDir + '\backend\branding.json';
    Json.SaveToFile(FilePath);
  finally
    Json.Free;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    AppDir := ExpandConstant('{app}');
    WriteBrandingJson(AppDir);
    PatchNginxConf(AppDir);
  end;
end;
