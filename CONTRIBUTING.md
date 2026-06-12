# Entwicklung

Privates Projekt — diese Datei sammelt die Konventionen und Build-Befehle für alle drei Apps.

## Bauen und Testen

**Windows** (Python 3.11+):

```bat
cd BlitzdiktatWin
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py
python -m pytest tests -q
```

**Android** (JDK 17, Android SDK):

```bat
cd BlitzdiktatAndroid
gradlew.bat :app:testDebugUnitTest :app:assembleDebug
```

**macOS** (Xcode, XcodeGen):

```bash
./build.sh --debug
```

Die CI (`.github/workflows/ci.yml`) führt bei jedem Push auf `main` alle drei Jobs aus: `check-windows` (ruff, compileall, pytest), `check-android` (JUnit + Debug-APK), `build-macos` (inkl. Secret-Scan).

## Konventionen

- Kleine, fokussierte Commits mit aussagekräftiger Message; CI muss grün bleiben.
- Die drei Apps spiegeln sich gegenseitig: gleiche Workflows, gleiche Prompts, gleiche Begriffe. Wer ein Feature auf einer Plattform ändert, prüft, ob die anderen nachziehen sollten (siehe [ROADMAP.md](ROADMAP.md)).
- Neue rein-logische Bausteine testbar halten (auf Android: Context-frei, damit JVM-Tests laufen).
- Keine Telemetrie, keine zusätzlichen Dienste, kein eingebetteter API-Key.
- Niemals Secrets committen: keine API-Keys, Tokens, Keystores (`key.properties`, `*.jks`), privaten Aufnahmen oder Transkripte. Die CI prüft Muster aus `.github/secret-scan-patterns.txt`.
- Ehrlich dokumentieren: OpenAI-Workflows nicht als „offline" oder „lokal" beschreiben.
