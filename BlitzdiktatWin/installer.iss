; ============================================================================
; Blitzdiktat – Inno Setup Installer Script
; Voraussetzung: PyInstaller wurde bereits ausgeführt (dist\Blitzdiktat\ existiert)
;
; Erstellt: setup_blitzdiktat_<version>.exe
; ============================================================================

#define AppName      "Blitzdiktat"
#define AppVersion   "2.1.8"
#define AppPublisher "Thorben Meier"
#define AppURL       "https://github.com/Regdar76/Blitzdiktat"
#define AppExeName   "Blitzdiktat.exe"
#define DistDir      "dist\Blitzdiktat"

[Setup]
; --- Grundlegende Metadaten ---
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; --- Installationspfad ---
; Standardmäßig in Program Files; Admin-Rechte nicht zwingend erforderlich
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; --- Installer-Ausgabe ---
OutputDir=C:\Github
OutputBaseFilename=Setup Blitzdiktat {#AppVersion}
SetupIconFile=resources\blitzdiktat.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; --- Windows-Anforderungen ---
MinVersion=10.0
PrivilegesRequiredOverridesAllowed=dialog

; --- Aussehen ---
WizardStyle=modern
WizardResizable=yes
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes

; --- Sonstiges ---
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} – KI-gestützte Spracheingabe für Windows

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Desktop-Verknüpfung erstellen";   GroupDescription: "Zusätzliche Symbole:"; Flags: unchecked
Name: "startupicon";    Description: "Beim Windows-Start automatisch laden"; GroupDescription: "Autostart:"; Flags: unchecked

[Files]
; Gesamten PyInstaller-Output einschließen
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Whisper-Small-Modell vorab einbündeln (in AppData des Nutzers ablegen)
Source: "dist\whisper_models\*"; DestDir: "{userappdata}\Blitzdiktat\whisper_models"; \
    Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Check: WhisperModelExists

[Icons]
; Startmenü
Name: "{group}\{#AppName}";                    Filename: "{app}\{#AppExeName}"
Name: "{group}\{#AppName} deinstallieren";     Filename: "{uninstallexe}"

; Optionaler Desktop-Icon (nur wenn Task gewählt)
Name: "{autodesktop}\{#AppName}";              Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Autostart-Eintrag (nur wenn Task gewählt)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#AppName}"; \
    ValueData: """{app}\{#AppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; App direkt nach Installation starten (optional)
Filename: "{app}\{#AppExeName}"; \
    Description: "{#AppName} jetzt starten"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; Laufende Instanz vor Deinstallation beenden
Filename: "taskkill.exe"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden; RunOnceId: "KillBlitzdiktat"

[UninstallDelete]
; Nutzerdaten im AppData-Ordner NICHT löschen (API-Keys bleiben erhalten)
; Nur temporäre Audiodateien entfernen
Type: filesandordirs; Name: "{userappdata}\Blitzdiktat\recordings"

[Code]
// ── Prüft ob das vorgebaute Whisper-Modell im Source-Verzeichnis vorhanden ist
function WhisperModelExists(): Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\dist\whisper_models'));
end;

// ── Prüft ob eine ältere Version läuft und warnt den Nutzer ─────────────────
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Laufende Instanz beenden falls vorhanden
  Exec('taskkill.exe', '/f /im Blitzdiktat.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ── Deinstallation: Nutzer fragen ob AppData-Ordner gelöscht werden soll ────
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataPath: String;
  Answer: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\Blitzdiktat');
    if DirExists(AppDataPath) then
    begin
      Answer := MsgBox(
        'Sollen alle Blitzdiktat-Einstellungen und gespeicherten Whisper-Modelle ebenfalls gelöscht werden?' + #13#10 +
        '(API-Keys, Einstellungen, heruntergeladene Modelle)' + #13#10#13#10 +
        'Pfad: ' + AppDataPath,
        mbConfirmation, MB_YESNO
      );
      if Answer = IDYES then
        DelTree(AppDataPath, True, True, True);
    end;
  end;
end;
