; ============================================================================
; Testinstaller für den Baustein "Lokale KI" (BlitzdiktatWin\installer_lokale_ki.iss)
;
; Spielt die beiden Downloads samt Prüfsummen-Prüfung durch, ohne den Rechner
; zu verändern: Alles landet im gewählten Zielordner, LM Studio wird nur
; heruntergeladen (nicht installiert), es gibt keinen Registry-Eintrag und
; keinen Uninstaller. Nach dem Test den Zielordner einfach löschen.
;
; Bauen:    ISCC.exe /O<Ausgabeordner> lokale_ki_test.iss
; Starten:  lokale-ki-test.exe /VERYSILENT /SUPPRESSMSGBOXES /TASKS=localai
;               /DIR=<Zielordner> /LOG=<Zielordner>.log
; Erwartet: <Zielordner>\modelle\gemma-4-E2B-it-Q4_K_M.gguf
;           <Zielordner>\Setup-Dateien\LM-Studio-Setup.exe
;           <Zielordner>\vorgabe\lokale_ki_einrichten.json
; ============================================================================

#define LokaleKiTest
#define ModelDir  "{app}\modelle"
#define MarkerDir "{app}\vorgabe"

[Setup]
AppName=Blitzdiktat-Installertest
AppVersion=0
DefaultDirName={localappdata}\Temp\Blitzdiktat-Installertest
PrivilegesRequired=lowest
Uninstallable=no
CreateUninstallRegKey=no
DisableProgramGroupPage=yes
OutputBaseFilename=lokale-ki-test
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

#include "..\..\BlitzdiktatWin\installer_lokale_ki.iss"
