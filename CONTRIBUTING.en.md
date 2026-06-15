# Development

> 🌐 [Deutsch](CONTRIBUTING.md) · **English**

Private project — this file collects the conventions and build commands for all three apps.

## Building and Testing

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

The CI (`.github/workflows/ci.yml`) runs all three jobs on every push to `main`: `check-windows` (ruff, compileall, pytest), `check-android` (JUnit + debug APK), `build-macos` (including a secret scan).

## Conventions

- Small, focused commits with a meaningful message; CI must stay green.
- The three apps mirror each other: same workflows, same prompts, same terms. Whoever changes a feature on one platform checks whether the others should follow suit (see [ROADMAP.en.md](ROADMAP.en.md)).
- Keep new purely logical building blocks testable (on Android: context-free, so the JVM tests run).
- No telemetry, no additional services, no embedded API key.
- Never commit secrets: no API keys, tokens, keystores (`key.properties`, `*.jks`), private recordings, or transcripts. The CI checks patterns from `.github/secret-scan-patterns.txt`.
- Document honestly: do not describe OpenAI workflows as "offline" or "local".
