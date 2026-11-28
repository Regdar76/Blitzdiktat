; ============================================================================
; Blitzdiktat – Inno Setup Installer Script
; Voraussetzung: PyInstaller wurde bereits ausgeführt (dist\Blitzdiktat\ existiert)
;
; Erstellt: setup_blitzdiktat_<version>.exe
; ============================================================================

#define AppName      "Blitzdiktat"
#define AppVersion   "2.2.0"
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

; --- Windows-Anforderungen ---
MinVersion=10.0
; Alles (App, Whisper-Modell, LM Studio, Einstellungen) liegt im Benutzerprofil:
; keine Administrator-Abfrage nötig und keine Auswahl für den Anwender.
PrivilegesRequired=lowest

; --- Ablauf: keine Fragen. Nur der Fortschrittsbalken, danach startet Blitzdiktat.
WizardStyle=modern
ShowLanguageDialog=no
DisableWelcomePage=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
DisableProgramGroupPage=yes

; --- Sonstiges ---
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} – KI-gestützte Spracheingabe für Windows

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"

; Die Aufgabe "localai" (lokale KI) steht in installer_lokale_ki.iss. Die
; Aufgabenseite wird übersprungen (siehe ShouldSkipPage); es gelten die Vorgaben.

[Files]
; Gesamten PyInstaller-Output einschließen
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Whisper-Small-Modell vorab einbündeln (in AppData des Nutzers ablegen)
Source: "dist\whisper_models\*"; DestDir: "{userappdata}\Blitzdiktat\whisper_models"; \
    Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
; Startmenü
Name: "{group}\{#AppName}";                    Filename: "{app}\{#AppExeName}"
Name: "{group}\{#AppName} deinstallieren";     Filename: "{uninstallexe}"

[Registry]
; Autostart: Blitzdiktat muss laufen, damit die Tastenkürzel funktionieren.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#AppName}"; \
    ValueData: """{app}\{#AppExeName}"""; \
    Flags: uninsdeletevalue; Check: IsFreshInstall

[Run]
; Blitzdiktat startet nach der Installation von selbst (nicht bei /SILENT).
Filename: "{app}\{#AppExeName}"; Flags: nowait skipifsilent

[UninstallRun]
; Laufende Instanz vor Deinstallation beenden
Filename: "taskkill.exe"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden; RunOnceId: "KillBlitzdiktat"

[UninstallDelete]
; Nutzerdaten im AppData-Ordner NICHT löschen (API-Keys bleiben erhalten)
; Audioaufnahmen sind sensibel und werden immer entfernt — sie liegen unter
; %LOCALAPPDATA%\Blitzdiktat\Audioaufnahmen (nicht {userappdata}\recordings)
Type: filesandordirs; Name: "{localappdata}\Blitzdiktat\Audioaufnahmen"

; Lokale KI (LM Studio + Gemma 4 E2B): eigener Baustein mit Aufgabe, Downloads
; und Einrichtung. Muss vor dem [Code]-Abschnitt unten eingebunden werden.
#include "installer_lokale_ki.iss"

[Code]
var
  // War Blitzdiktat schon installiert? Dann ist dies ein Update.
  WasInstalled: Boolean;

// ── Autostart nur bei der ersten Installation eintragen ────────────────────
// Bei Updates bleibt die Wahl des Anwenders (Einstellungen → Windows-Start) erhalten.
function IsFreshInstall(): Boolean;
begin
  Result := not WasInstalled;
end;

// ── Keine Auswahlseiten: Aufgaben (lokale KI) gelten mit ihren Vorgaben ────
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = wpSelectTasks);
end;

// ── Prüft ob eine ältere Version läuft und warnt den Nutzer ─────────────────
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  WasInstalled := RegKeyExists(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}_is1');
  // Laufende Instanz beenden falls vorhanden
  Exec('taskkill.exe', '/f /im Blitzdiktat.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ── Deinstallation: Nutzer fragen ob alle App-Daten gelöscht werden sollen ──
// Es gibt zwei Datenorte:
//   {userappdata}\Blitzdiktat   – Einstellungen, Whisper-Modelle
//   {localappdata}\Blitzdiktat  – Transkriptionen, Protokoll-PDFs
//     (Audioaufnahmen darunter werden via [UninstallDelete] immer entfernt)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RoamingPath, LocalPath: String;
  Answer: Integer;
begin
  // Lokale KI (LM Studio, Modelle) zuerst, solange die Merkdatei noch da ist.
  if CurUninstallStep = usUninstall then
    RemoveLocalAi();

  if CurUninstallStep = usPostUninstall then
  begin
    RoamingPath := ExpandConstant('{userappdata}\Blitzdiktat');
    LocalPath := ExpandConstant('{localappdata}\Blitzdiktat');
    if DirExists(RoamingPath) or DirExists(LocalPath) then
    begin
      Answer := MsgBox(
        'Sollen alle Blitzdiktat-Daten ebenfalls gelöscht werden?' + #13#10 +
        '(Einstellungen, heruntergeladene Whisper-Modelle, Transkriptionen und Protokolle)' + #13#10#13#10 +
        'Pfade:' + #13#10 +
        RoamingPath + #13#10 +
        LocalPath,
        mbConfirmation, MB_YESNO
      );
      if Answer = IDYES then
      begin
        if DirExists(RoamingPath) then
          DelTree(RoamingPath, True, True, True);
        if DirExists(LocalPath) then
          DelTree(LocalPath, True, True, True);
      end;
    end;
  end;
end;
