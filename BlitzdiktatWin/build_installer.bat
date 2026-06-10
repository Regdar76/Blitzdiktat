@echo off
setlocal EnableDelayedExpansion
:: ============================================================================
:: Blitzdiktat – Windows Installer Build Script
::
:: Erstellt:  C:\Github\Setup Blitzdiktat 1.1.2.exe
::
:: Voraussetzungen (werden automatisch geprüft):
::   - Python 3.11+
::   - PyInstaller  (pip install pyinstaller)
::   - Inno Setup 6 (https://jrsoftware.org/isdl.php)  – für den Setup-Wizard
::
:: Schnellstart:
::   Doppelklick auf build_installer.bat  ODER
::   build_installer.bat [--skip-innosetup]
:: ============================================================================

title Blitzdiktat Installer Build

set "SKIP_INNO=0"
if "%1"=="--skip-innosetup" set "SKIP_INNO=1"

echo.
echo  ==========================================
echo   Blitzdiktat ^| Installer Build
echo  ==========================================
echo.

:: ── Verzeichnis sicherstellen ────────────────────────────────────────────────
cd /d "%~dp0"

:: ── Python prüfen ────────────────────────────────────────────────────────────
echo [1/5] Python prüfen...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  FEHLER: Python wurde nicht gefunden.
    echo  Bitte Python 3.11+ von https://python.org/downloads installieren
    echo  und sicherstellen, dass "Python zum PATH hinzufügen" aktiviert ist.
    echo.
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo  OK – Python %PYVER%

:: ── PyInstaller installieren / prüfen ───────────────────────────────────────
echo [2/5] PyInstaller prüfen...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo  PyInstaller nicht gefunden – wird installiert...
    python -m pip install --upgrade pyinstaller
    if errorlevel 1 (
        echo  FEHLER: PyInstaller konnte nicht installiert werden.
        pause & exit /b 1
    )
)
for /f %%v in ('python -m PyInstaller --version 2^>^&1') do set "PIVER=%%v"
echo  OK – PyInstaller %PIVER%

:: ── Abhängigkeiten installieren ──────────────────────────────────────────────
echo [3/5] Abhängigkeiten installieren / aktualisieren...
python -m pip install --upgrade ^
    openai ^
    pystray ^
    pillow ^
    pynput ^
    sounddevice ^
    numpy ^
    keyring ^
    customtkinter ^
    pywin32 ^
    faster-whisper ^
    httpx ^
    reportlab
if errorlevel 1 (
    echo  WARNUNG: Einige Pakete konnten nicht aktualisiert werden.
    echo  Der Build wird trotzdem fortgesetzt.
)
echo  OK

:: ── Icon prüfen ───────────────────────────────────────────────────────────────
if not exist "resources\blitzdiktat.ico" (
    echo  Icon wird generiert...
    python resources\make_icon.py
)

:: ── Whisper-Modell vorausladen ────────────────────────────────────────────────
echo [4/5] Whisper-Small-Modell vorausladen...
python download_model_for_build.py
if errorlevel 1 (
    echo  WARNUNG: Modell konnte nicht heruntergeladen werden.
    echo  Der Installer wird ohne vorinstalliertes Modell erstellt.
    echo  Das Modell wird beim ersten App-Start automatisch geladen.
)
echo.

:: ── PyInstaller ausführen ────────────────────────────────────────────────────
echo [4b/5] PyInstaller – App bündeln...
echo.

if exist "dist\Blitzdiktat" (
    echo  Altes dist\Blitzdiktat\ wird gelöscht...
    rmdir /s /q "dist\Blitzdiktat"
)
if exist "build" (
    rmdir /s /q "build"
)

python -m PyInstaller blitzdiktat.spec --noconfirm
if errorlevel 1 (
    echo.
    echo  FEHLER: PyInstaller schlug fehl.
    echo  Prüfe die Ausgabe oben auf Fehlermeldungen.
    pause & exit /b 1
)

echo.
echo  OK – Standalone-App: dist\Blitzdiktat\Blitzdiktat.exe

:: ── Kurztest: Startet die exe überhaupt? ────────────────────────────────────
echo  Starte kurzen Smoke-Test (3 Sekunden)...
start "" /B "dist\Blitzdiktat\Blitzdiktat.exe"
timeout /t 3 /nobreak >nul
taskkill /f /im Blitzdiktat.exe >nul 2>&1
echo  OK – Smoke-Test bestanden

:: ── Inno Setup ausführen ─────────────────────────────────────────────────────
if "%SKIP_INNO%"=="1" (
    echo.
    echo  Inno Setup übersprungen ^(--skip-innosetup^).
    goto :done
)

echo [5/5] Inno Setup – Installer erstellen...

:: Typische Installationspfade von Inno Setup 6
set "ISCC="
for %%p in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist "%%~p" set "ISCC=%%~p"
)

if "!ISCC!"=="" (
    echo.
    echo  Inno Setup nicht gefunden.
    echo  Bitte von https://jrsoftware.org/isdl.php installieren,
    echo  dann erneut ausführen  ODER  mit --skip-innosetup überspringen.
    echo.
    echo  Die gebündelte App liegt bereits unter:
    echo    dist\Blitzdiktat\Blitzdiktat.exe
    echo.
    pause & exit /b 0
)

if not exist "C:\Github" mkdir "C:\Github"

"!ISCC!" installer.iss
if errorlevel 1 (
    echo.
    echo  FEHLER: Inno Setup schlug fehl.
    pause & exit /b 1
)

:done
echo.
echo  ==========================================
echo   Build erfolgreich abgeschlossen!
echo  ==========================================
echo.
if exist "C:\Github\Setup Blitzdiktat 1.1.2.exe" (
    echo  Installer:    C:\Github\Setup Blitzdiktat 1.1.2.exe
)
echo  Standalone:   dist\Blitzdiktat\Blitzdiktat.exe
echo.
echo  Der Installer kann jetzt an andere weitergegeben werden.
echo  Alle Abhängigkeiten sind enthalten – Python muss auf dem
echo  Zielrechner NICHT installiert sein.
echo.
pause
