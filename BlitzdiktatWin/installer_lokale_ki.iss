; ============================================================================
; Blitzdiktat – Installer-Baustein "Lokale KI"
;
; Wird von installer.iss eingebunden. Richtet auf Wunsch die Textverarbeitung
; ohne Internet ein:
;   1. LM Studio herunterladen (offizielle Adresse des Herstellers) und
;      still installieren – nur wenn es noch nicht installiert ist.
;   2. Das Sprachmodell Gemma 4 E2B von Hugging Face herunterladen und in den
;      Modellordner von LM Studio legen – nur wenn es dort noch fehlt.
;   3. Eine kleine Vorgabe-Datei ablegen; Blitzdiktat stellt sich damit beim
;      nächsten Start auf "Eigener Server" mit diesem Modell um und startet
;      den Server von LM Studio künftig selbst.
;
; Beide Downloads sind auf eine feste Version festgelegt und werden über ihre
; SHA-256-Prüfsumme geprüft. Beides wird NICHT mit dem Installer ausgeliefert:
; zusammen wären es über 4 GB (GitHub erlaubt 2 GB je Datei), und LM Studio
; darf nur vom Hersteller verteilt werden.
;
; Neue LM-Studio-Version eintragen:  winget show --id ElementLabs.LMStudio -e
; (liefert Adresse und Prüfsumme), Größe in Bytes aus dem Download.
; ============================================================================

#define LMStudioVersion "0.4.29-2"
#define LMStudioUrl     "https://installers.lmstudio.ai/win32/x64/" + LMStudioVersion + "/LM-Studio-" + LMStudioVersion + "-x64.exe"
#define LMStudioSha256  "969dc4f02f44b215fc68e3ba71f6832359b688e71fd7b0c02d863fbb536c9647"
#define LMStudioBytes   "654595456"
#define LMSetupName     "LM-Studio-Setup.exe"

; Gemma 4 E2B (Apache-2.0), 4-Bit-Fassung von lmstudio-community, fester Stand
#define GemmaFile       "gemma-4-E2B-it-Q4_K_M.gguf"
#define GemmaUrl        "https://huggingface.co/lmstudio-community/gemma-4-E2B-it-GGUF/resolve/eed445ccfb8aef2e279df1a97e133baf06e443b4/" + GemmaFile
#define GemmaSha256     "71e6e8cb64a76da1a734fb8f6ba389d2784950d9902f5e87244fca0a15190c94"
#define GemmaBytes      "3427880384"
; Name, unter dem LM Studio dieses Modell anbietet
#define GemmaModelId    "gemma-4-e2b-it"

; Zielordner – für den Installer-Test (tools\installertest) überschreibbar
#ifndef ModelDir
  #define ModelDir   "{%USERPROFILE}\.lmstudio\models\lmstudio-community\gemma-4-E2B-it-GGUF"
#endif
#ifndef MarkerDir
  #define MarkerDir  "{userappdata}\Blitzdiktat"
#endif
; Muss für den nicht erhöhten Benutzer lesbar sein ({tmp} ist es nicht).
#define LMSetupDir   "{app}\Setup-Dateien"

[Tasks]
Name: "localai"; \
    Description: "LM Studio und das Sprachmodell Gemma 4 E2B herunterladen und einrichten (Download ca. 4,1 GB). Es gelten die Bedingungen von LM Studio (lmstudio.ai/terms) und die Lizenz von Gemma (Apache 2.0)."; \
    GroupDescription: "Lokale KI – Textverarbeitung ohne Internet und ohne OpenAI-Schlüssel:"; \
    Flags: checkedonce

[Files]
Source: "{#LMStudioUrl}"; DestName: "{#LMSetupName}"; DestDir: "{#LMSetupDir}"; \
    Hash: "{#LMStudioSha256}"; ExternalSize: {#LMStudioBytes}; \
    Flags: external download ignoreversion; Tasks: localai; Check: NeedLMStudio

Source: "{#GemmaUrl}"; DestName: "{#GemmaFile}"; DestDir: "{#ModelDir}"; \
    Hash: "{#GemmaSha256}"; ExternalSize: {#GemmaBytes}; \
    Flags: external download ignoreversion uninsneveruninstall; Tasks: localai; Check: NeedGemma

[Code]
var
  LMStudioTestDone: Boolean;
  // Was schon vor diesem Setup da war – nur was das Setup selbst installiert,
  // wird bei der Deinstallation wieder entfernt.
  LMStudioPreExisting: Boolean;
  GemmaPreExisting: Boolean;
  // Gab es den Datenordner von LM Studio (.lmstudio: Modelle, Chats) schon vorher?
  // Dann gehört er dem Anwender und wird nie gelöscht – auch wenn das Programm
  // an einem unüblichen Ort lag und deshalb als "nicht installiert" erkannt wurde.
  LMStudioDataPreExisting: Boolean;

// ── Ist LM Studio schon installiert? ────────────────────────────────────────
function LMStudioInstalled(): Boolean;
begin
#ifdef LokaleKiTest
  // Im Installer-Test wird LM Studio nur heruntergeladen, nicht installiert.
  Result := LMStudioTestDone;
#else
  Result := FileExists(ExpandConstant('{localappdata}\Programs\LM Studio\LM Studio.exe'))
         or FileExists(ExpandConstant('{localappdata}\Programs\Bionic\Bionic.exe'))
         or FileExists(ExpandConstant('{%ProgramW6432}\LM Studio\LM Studio.exe'));
#endif
end;

// ── Liegt das Modell vollständig im Modellordner? ───────────────────────────
function GemmaModelPresent(): Boolean;
var
  Size: Int64;
begin
  Result := FileSize64(ExpandConstant('{#ModelDir}\{#GemmaFile}'), Size)
            and (Size = {#GemmaBytes});
end;

function NeedLMStudio(): Boolean;
begin
  Result := not LMStudioInstalled();
end;

function NeedGemma(): Boolean;
begin
  Result := not GemmaModelPresent();
end;

// ── Zu wenig Platz: lokale KI stillschweigend weglassen (keine Rückfrage) ───
// Blitzdiktat selbst läuft auch ohne; die KI lässt sich später einrichten.
procedure InitializeWizard();
var
  FreeBytes, TotalBytes: Int64;
begin
  LMStudioPreExisting := LMStudioInstalled();
  GemmaPreExisting := GemmaModelPresent();
  LMStudioDataPreExisting := DirExists(ExpandConstant('{%USERPROFILE}\.lmstudio'));
  if GetSpaceOnDisk64(ExpandConstant('{%USERPROFILE}'), FreeBytes, TotalBytes) then
    if FreeBytes < Int64(10) * 1073741824 then
    begin
      WizardSelectTasks('!localai');
      Log('Lokale KI: weniger als 10 GB frei, wird übersprungen.');
    end;
end;

// ── Was gehört Blitzdiktat? (Merkdatei neben der Vorgabe) ───────────────────
function OwnershipFile(): String;
begin
  Result := ExpandConstant('{#MarkerDir}\lokale_ki_installiert.json');
end;

function Owns(Flag: String): Boolean;
var
  Content: AnsiString;
begin
  Result := LoadStringFromFile(OwnershipFile(), Content)
            and (Pos('"' + Flag + '": true', String(Content)) > 0);
end;

function BoolText(Value: Boolean): String;
begin
  if Value then Result := 'true' else Result := 'false';
end;

// Merkt sich, was dieses Setup installiert hat. Ein früheres "true" bleibt
// erhalten (bei Updates ist LM Studio dann schon da, gehört aber weiter uns).
procedure RememberOwnership();
begin
  ForceDirectories(ExpandConstant('{#MarkerDir}'));
  SaveStringToFile(OwnershipFile(),
    '{"lmstudio": ' + BoolText(Owns('lmstudio') or (not LMStudioPreExisting)) +
    ', "gemma": ' + BoolText(Owns('gemma') or (not GemmaPreExisting)) +
    ', "lmstudio_data": ' + BoolText(Owns('lmstudio_data')
        or ((not LMStudioPreExisting) and (not LMStudioDataPreExisting))) + '}',
    False);
end;

// ── Deinstallation: lokale KI entfernen, soweit Blitzdiktat sie installiert hat
procedure RemoveLocalAi();
var
  ResultCode: Integer;
  AppDir, Uninstaller, GemmaDir: String;
  OwnsData: Boolean;
begin
  OwnsData := Owns('lmstudio_data');
  GemmaDir := ExpandConstant('{%USERPROFILE}\.lmstudio\models\lmstudio-community\gemma-4-E2B-it-GGUF');
  if Owns('lmstudio') then
  begin
    Exec('taskkill.exe', '/f /im "LM Studio.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/f /im lms.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    AppDir := ExpandConstant('{localappdata}\Programs\LM Studio');
    Uninstaller := AppDir + '\Uninstall LM Studio.exe';
    // "_?=" lässt den Uninstaller an Ort und Stelle laufen, damit wir auf ihn warten können.
    if FileExists(Uninstaller) then
      Exec(Uninstaller, '/currentuser /S _?=' + AppDir, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    // Programm, Updater, Verknüpfungen, Autostart.
    DelTree(AppDir, True, True, True);
    DelTree(ExpandConstant('{localappdata}\lm-studio-updater'), True, True, True);
    // Modelle, Chats und Einstellungen nur, wenn der Datenordner erst durch uns entstand.
    if OwnsData then
    begin
      DelTree(ExpandConstant('{%USERPROFILE}\.lmstudio'), True, True, True);
      DelTree(ExpandConstant('{userappdata}\LM Studio'), True, True, True);
    end
    else if Owns('gemma') then
      DelTree(GemmaDir, True, True, True);
    DeleteFile(ExpandConstant('{userdesktop}\LM Studio.lnk'));
    DeleteFile(ExpandConstant('{userprograms}\LM Studio.lnk'));
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'electron.app.LM Studio');
    Log('Lokale KI: LM Studio und Zubehör entfernt.');
  end
  else if Owns('gemma') then
  begin
    // LM Studio war vorher da: nur das von uns geladene Modell entfernen.
    DelTree(GemmaDir, True, True, True);
    Log('Lokale KI: Modell entfernt (LM Studio bleibt, es war schon vorher installiert).');
  end;
  DeleteFile(OwnershipFile());
end;

// ── Nach dem Kopieren: LM Studio installieren, Vorgabe für die App ablegen ──
procedure SetUpLocalAi();
var
  SetupFile, MarkerFile: String;
  ResultCode: Integer;
begin
  SetupFile := ExpandConstant('{#LMSetupDir}\{#LMSetupName}');
  if FileExists(SetupFile) then
  begin
#ifdef LokaleKiTest
    LMStudioTestDone := True;
#else
    if not LMStudioInstalled() then
    begin
      WizardForm.StatusLabel.Caption := 'Lokale KI wird eingerichtet …';
      WizardForm.FilenameLabel.Caption := '';
      // Als der angemeldete Benutzer (LM Studio installiert sich in das
      // Benutzerprofil), ohne sichtbares Fenster.
      if not ExecAsOriginalUser(SetupFile, '/S', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
        Log('LM Studio: Installer konnte nicht gestartet werden, Code ' + IntToStr(ResultCode))
      else
        Log('LM Studio: Installer beendet mit Code ' + IntToStr(ResultCode));
      // Der Anwender soll von LM Studio nichts bemerken: ein vom Installer
      // gestartetes Fenster schließen, die Desktop-Verknüpfung entfernen.
      // (Nur hier, wo LM Studio gerade erst neu installiert wurde.)
      Exec('taskkill.exe', '/f /im "LM Studio.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      DeleteFile(ExpandConstant('{userdesktop}\LM Studio.lnk'));
    end;
    DeleteFile(SetupFile);
    RemoveDir(ExpandConstant('{#LMSetupDir}'));
#endif
  end;

  // Merken, was wir installiert haben – auch wenn danach etwas schiefgeht,
  // damit die Deinstallation nichts zurücklässt.
  RememberOwnership();

  if GemmaModelPresent() and LMStudioInstalled() then
  begin
    MarkerFile := ExpandConstant('{#MarkerDir}\lokale_ki_einrichten.json');
    ForceDirectories(ExpandConstant('{#MarkerDir}'));
    SaveStringToFile(MarkerFile,
      '{"provider": "custom", "base_url": "http://localhost:1234/v1", "model": "{#GemmaModelId}"}',
      False);
    Log('Lokale KI: Vorgabe für Blitzdiktat abgelegt.');
  end
  else
    Log('Lokale KI: LM Studio oder das Modell fehlt - nicht eingerichtet.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('localai') then
    SetUpLocalAi();
end;
