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

// ── Vor dem Start warnen, wenn der Platz knapp ist ──────────────────────────
function NextButtonClick(CurPageID: Integer): Boolean;
var
  FreeBytes, TotalBytes: Int64;
  FreeGB: Integer;
begin
  Result := True;
  if (CurPageID = wpSelectTasks) and WizardIsTaskSelected('localai') then
  begin
    if GetSpaceOnDisk64(ExpandConstant('{%USERPROFILE}'), FreeBytes, TotalBytes) then
    begin
      FreeGB := FreeBytes div 1073741824;
      if FreeGB < 10 then
        Result := SuppressibleMsgBox(
          'Für die lokale KI werden etwa 10 GB freier Speicher gebraucht ' +
          '(während des Downloads kurzzeitig mehr als danach).' + #13#10 +
          'Frei sind nur ' + IntToStr(FreeGB) + ' GB.' + #13#10#13#10 +
          'Trotzdem fortfahren?',
          mbConfirmation, MB_YESNO, IDYES) = IDYES;
    end;
  end;
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
      WizardForm.StatusLabel.Caption := 'LM Studio wird installiert …';
      WizardForm.FilenameLabel.Caption := '';
      // Als der angemeldete Benutzer, nicht als Administrator: LM Studio
      // installiert sich in das Benutzerprofil.
      if not ExecAsOriginalUser(SetupFile, '/S', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
        Log('LM Studio: Installer konnte nicht gestartet werden, Code ' + IntToStr(ResultCode))
      else
        Log('LM Studio: Installer beendet mit Code ' + IntToStr(ResultCode));
    end;
    DeleteFile(SetupFile);
    RemoveDir(ExpandConstant('{#LMSetupDir}'));
#endif
  end;

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
    SuppressibleMsgBox(
      'Die lokale KI konnte nicht vollständig eingerichtet werden ' +
      '(LM Studio oder das Sprachmodell fehlt).' + #13#10#13#10 +
      'Blitzdiktat selbst ist installiert. Das Setup kann später noch einmal ' +
      'gestartet werden, oder LM Studio wird von Hand eingerichtet: ' +
      'Einstellungen → „KI für die Textverarbeitung“.',
      mbInformation, MB_OK, IDOK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('localai') then
    SetUpLocalAi();
end;
