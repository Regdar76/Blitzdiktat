# Blitzdiktat for Android

> 🌐 [Deutsch](README.md) · **English**

Android version of [Blitzdiktat](../README.en.md): dictation via
on-device speech recognition (offline, no API key) plus the familiar
LLM workflows with your own OpenAI key (BYO key, securely encrypted in the
Android Keystore).

**Deliberately NO embedded API key:** keys in distributed apps can be
extracted within minutes and lead to abuse at someone else's expense.

## Components

| Component | Description |
|---|---|
| **App** | Workflow cards like on Windows: record → process → copy/share |
| **Keyboard (IME)** | Mic key in any app: speak → text lands directly in the input field |
| **History** | All results are stored locally (14 days, like on Windows) |

Workflows: Blitzdiktat (local, no key), Blitzdiktat+, $%&!, :) and Protokoll
(require an OpenAI key).

## Features

- **History**: Every workflow result is automatically stored as a `.txt` in
  the app storage (minutes additionally as a PDF) and cleaned up after 14 days
  — viewable in the "History" tab with copy/share/delete.
- **Minutes as PDF**: The finished minutes are saved as a formatted PDF
  and can be shared directly.
- **Minutes from a text file**: An existing text/Markdown file (e.g.
  a raw transcript) can be imported and processed into minutes.
  (Audio import requires Whisper on-device and remains on the roadmap, see below.)
- **Settings**: Dictation language (default `de-DE`), tone, emoji density,
  OpenAI model overrides as well as custom names and system prompts per workflow —
  just like in the Windows app.
- **Vocabulary**: Proper names and technical terms that speech recognition often
  spells incorrectly can be entered correctly in the settings.
  In addition, the app learns automatically like on Windows: after every
  workflow with an OpenAI key, proper names are extracted in the background
  (max. 150, the oldest are dropped first). Both feed into the
  prompts of Blitzdiktat+ and Protokoll. Limitation compared to Windows:
  for plain Blitzdiktat the vocabulary cannot be taken into account,
  because Android's device speech recognition does not accept a term list
  (Whisper on-device would solve this, see roadmap).

## Technology

- Kotlin + Jetpack Compose (app), classic Views (keyboard)
- Dictation: `SpeechRecognizer` with `EXTRA_PREFER_OFFLINE` — uses the
  device's on-device recognition (offline on current devices; if needed, load
  the matching offline language pack under Settings → System → Language)
- LLM: OpenAI Chat Completions via OkHttp, models like on Windows
  (`gpt-4o-mini` / `gpt-4o`, overridable in the settings)
- Key storage: `EncryptedSharedPreferences` (AES-256, Android Keystore)
- PDF: `android.graphics.pdf.PdfDocument`, shared via a `FileProvider`
- minSdk 26 (Android 8.0), targetSdk 35

Upgrade path: for Whisper-quality offline (and audio file import), whisper.cpp
can later be integrated via JNI (NDK build + model download
required).

## Building

```bat
cd BlitzdiktatAndroid
gradlew.bat assembleDebug
```

(Linux/macOS: `./gradlew assembleDebug`.) The Gradle wrapper downloads Gradle
itself; only JDK 17 and the Android SDK (`local.properties` with
`sdk.dir=…`) need to be present. Or simply open the project in Android
Studio. The APK is then located under
`app/build/outputs/apk/debug/app-debug.apk`.

## Tests

```bat
gradlew.bat :app:testDebugUnitTest
```

The JVM unit tests cover prompt construction, history storage and the
workflow definitions. The CI job `check-android` runs them on every
push/PR and builds the debug APK.

## Release signing (optional)

For signed release builds, create a file `BlitzdiktatAndroid/key.properties`
(gitignored, never check it in):

```properties
storeFile=blitzdiktat-release.jks
storePassword=…
keyAlias=blitzdiktat
keyPassword=…
```

Create the keystore with `keytool -genkeypair -v -keystore blitzdiktat-release.jks
-keyalg RSA -keysize 2048 -validity 10000 -alias blitzdiktat`, then
`gradlew.bat assembleRelease`. Without `key.properties` an
unsigned release APK is produced.

## Installing (sideload)

1. Transfer the APK to the phone (USB, cloud, messenger to yourself …)
2. Tap the APK → allow installation from unknown sources once
3. Open the app → grant the microphone permission → optionally enter an API key
4. "Activate keyboard" → enable the Blitzdiktat keyboard
5. In any app: keyboard symbol at the bottom right → choose Blitzdiktat → 🎙️
