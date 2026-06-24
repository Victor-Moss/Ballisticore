; ============================================================================
;  BallistiCore — self-hosted Windows installer (Inno Setup 6+)
;
;  Produces a single Setup .exe that installs a fully self-contained,
;  offline, single-machine deployment:
;     - bundled Python (runs the FastAPI backend, which also serves the React UI)
;     - bundled portable PostgreSQL (data directory lives inside the install folder)
;     - launcher that starts everything on demand and opens the browser
;
;  All data stays on this machine. The only outbound traffic is optional
;  Twilio WhatsApp messages, and only when Twilio credentials are configured.
;
;  BEFORE COMPILING: run  build_payload.ps1  to stage the payload\ folder.
;  See BUILD.md for the full assembly + compile steps.
; ============================================================================

#define AppName        "BallistiCore"
#define AppVersion     "1.6.0"
#define AppPublisher   "BallistiCore"
#define AppURL         "https://ballisticore.co.za"

[Setup]
AppId={{1F6B3D2A-9C84-4E17-B5A2-7D9E4C1A8F30}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
DefaultDirName={userpf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=BallistiCore-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Per-user install: no admin rights needed, and the install folder is fully
; writable — required so PostgreSQL can own and write its data directory.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=assets\BallistiCore.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startupicon"; Description: "Start BallistiCore automatically when I sign in to Windows"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Dirs]
Name: "{app}\logs"
Name: "{app}\backend\permits"
Name: "{app}\config"

[Files]
; ── Bundled Python (embeddable + installed dependencies) ───────────────────
Source: "payload\python\*";   DestDir: "{app}\python";   Flags: recursesubdirs createallsubdirs ignoreversion
; ── Bundled portable PostgreSQL ────────────────────────────────────────────
Source: "payload\pgsql\*";    DestDir: "{app}\pgsql";    Flags: recursesubdirs createallsubdirs ignoreversion
; ── Backend (FastAPI) — excludes dev cruft and any local secrets ───────────
Source: "payload\backend\*";  DestDir: "{app}\backend";  Flags: recursesubdirs createallsubdirs ignoreversion; \
  Excludes: ".venv,__pycache__,*.pyc,tests,.pytest_cache,.env,permits\*"
; ── Built React frontend (the contents of dist\) ───────────────────────────
Source: "payload\frontend\*"; DestDir: "{app}\frontend"; Flags: recursesubdirs createallsubdirs ignoreversion
; ── Launcher + scripts ─────────────────────────────────────────────────────
Source: "launcher\BallistiCore.bat";      DestDir: "{app}"; Flags: ignoreversion
Source: "launcher\Stop BallistiCore.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "launcher\scripts\*";             DestDir: "{app}\scripts"; Flags: ignoreversion
; ── Client README ──────────────────────────────────────────────────────────
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
; ── App icon (used by the shortcuts) ───────────────────────────────────────
Source: "assets\BallistiCore.ico"; DestDir: "{app}"; Flags: ignoreversion
; ── Default branding (kept only if the user folder has none yet) ───────────
Source: "payload\backend\branding.json"; DestDir: "{app}\backend"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\{#AppName}";            Filename: "{app}\BallistiCore.bat";      WorkingDir: "{app}"; IconFilename: "{app}\BallistiCore.ico"; Comment: "Start BallistiCore and open it in your browser"
Name: "{group}\Stop {#AppName}";       Filename: "{app}\Stop BallistiCore.bat"; WorkingDir: "{app}"; IconFilename: "{app}\BallistiCore.ico"
Name: "{group}\BallistiCore README";   Filename: "{app}\README.txt"
Name: "{group}\Uninstall {#AppName}";  Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}";      Filename: "{app}\BallistiCore.bat";      WorkingDir: "{app}"; IconFilename: "{app}\BallistiCore.ico"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";      Filename: "{app}\BallistiCore.bat";      WorkingDir: "{app}"; IconFilename: "{app}\BallistiCore.ico"; Tasks: startupicon

[Run]
; First-run database setup: initdb, create role/db, write .env, run migrations.
Filename: "{app}\scripts\init_db.bat"; \
  StatusMsg: "Setting up the local database (first run may take a minute)..."; \
  Flags: waituntilterminated runhidden
; Offer to launch immediately when the wizard finishes.
Filename: "{app}\BallistiCore.bat"; Description: "Start {#AppName} now"; \
  WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

[UninstallRun]
; Make sure services are stopped before files are removed.
Filename: "{app}\scripts\stop_all.bat"; Flags: waituntilterminated runhidden; RunOnceId: "StopServices"

[Code]
{ ── Branding wizard page ───────────────────────────────────────────────── }
var
  BrandingPage: TInputQueryWizardPage;

procedure InitializeWizard();
begin
  BrandingPage := CreateInputQueryPage(wpSelectDir,
    'Company Branding',
    'Enter your company details.',
    'These appear on the login screen, the sidebar, and every printed permit. You can change them later under Admin > Company Details.');
  BrandingPage.Add('Company name:', False);
  BrandingPage.Add('PSIRA number (optional):', False);
  BrandingPage.Add('Permit number prefix (1-4 letters, e.g. BC):', False);
  BrandingPage.Values[0] := 'BallistiCore';
  BrandingPage.Values[1] := '';
  BrandingPage.Values[2] := 'BC';
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
      MsgBox('Company name is required.', mbError, MB_OK);
      Result := False; Exit;
    end;
    Prefix := UpperCase(Trim(BrandingPage.Values[2]));
    if (Length(Prefix) < 1) or (Length(Prefix) > 4) then
    begin
      MsgBox('Permit prefix must be 1-4 letters.', mbError, MB_OK);
      Result := False; Exit;
    end;
    BrandingPage.Values[2] := Prefix;
  end;
end;

{ Write branding.json from the wizard values. }
procedure WriteBrandingJson();
var
  Json: TStringList;
begin
  Json := TStringList.Create;
  try
    Json.Add('{');
    Json.Add('  "app_name": "BallistiCore",');
    Json.Add('  "company_name": "' + BrandingPage.Values[0] + '",');
    Json.Add('  "psira_number": "' + BrandingPage.Values[1] + '",');
    Json.Add('  "permit_prefix": "' + BrandingPage.Values[2] + '",');
    Json.Add('  "primary_color": "#1d4ed8"');
    Json.Add('}');
    Json.SaveToFile(ExpandConstant('{app}\backend\branding.json'));
  finally
    Json.Free;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteBrandingJson();
end;
