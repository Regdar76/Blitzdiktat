# Blitzdiktat für Android

Android-Version von [Blitzdiktat](../README.md): Diktieren per
On-Device-Spracherkennung (offline, ohne API-Key) plus die bekannten
LLM-Workflows mit eigenem OpenAI-Key (BYO-Key, sicher verschlüsselt im
Android Keystore).

**Bewusst KEIN eingebetteter API-Key:** Keys in verteilten Apps sind in
Minuten extrahierbar und führen zu Missbrauch auf fremde Rechnung.

## Komponenten

| Komponente | Beschreibung |
|---|---|
| **App** | Workflow-Karten wie auf Windows: aufnehmen → verarbeiten → kopieren/teilen |
| **Tastatur (IME)** | Mikro-Taste in jeder App: sprechen → Text landet direkt im Eingabefeld |
| **Verlauf** | Alle Ergebnisse werden lokal gespeichert (14 Tage, wie auf Windows) |

Workflows: Blitzdiktat (lokal, ohne Key), Blitzdiktat+, $%&!, :) und Protokoll
(benötigen OpenAI-Key).

## Funktionen

- **Verlauf**: Jedes Workflow-Ergebnis wird automatisch als `.txt` im
  App-Speicher abgelegt (Protokolle zusätzlich als PDF) und nach 14 Tagen
  bereinigt — einsehbar im Tab „Verlauf" mit Kopieren/Teilen/Löschen.
- **Protokoll als PDF**: Das fertige Protokoll wird als formatiertes PDF
  gespeichert und kann direkt geteilt werden.
- **Protokoll aus Textdatei**: Eine vorhandene Text-/Markdown-Datei (z. B.
  ein Rohtranskript) kann importiert und zum Protokoll verarbeitet werden.
  (Audio-Import braucht Whisper on-device und bleibt Roadmap, s. u.)
- **Einstellungen**: Diktiersprache (Standard `de-DE`), Ton, Emoji-Dichte,
  OpenAI-Modell-Overrides sowie eigene Namen und System-Prompts je Workflow —
  wie in der Windows-App.
- **Vokabular**: Eigennamen und Fachbegriffe, die die Spracherkennung oft
  falsch schreibt, lassen sich in den Einstellungen korrekt hinterlegen.
  Zusätzlich lernt die App wie auf Windows automatisch dazu: Nach jedem
  Workflow mit OpenAI-Key werden Eigennamen im Hintergrund extrahiert
  (max. 150, die ältesten fliegen zuerst raus). Beides fließt in die
  Prompts von Blitzdiktat+ und Protokoll ein. Grenze gegenüber Windows:
  Beim reinen Blitzdiktat kann das Vokabular nicht berücksichtigt werden,
  weil Androids Geräte-Spracherkennung keine Begriffsliste annimmt
  (Whisper on-device würde das lösen, s. Roadmap).

## Technik

- Kotlin + Jetpack Compose (App), klassische Views (Tastatur)
- Diktat: `SpeechRecognizer` mit `EXTRA_PREFER_OFFLINE` — nutzt die
  On-Device-Erkennung des Geräts (auf aktuellen Geräten offline; ggf. unter
  Einstellungen → System → Sprache das passende Offline-Sprachpaket laden)
- LLM: OpenAI Chat Completions via OkHttp, Modelle wie auf Windows
  (`gpt-4o-mini` / `gpt-4o`, überschreibbar in den Einstellungen)
- Key-Speicherung: `EncryptedSharedPreferences` (AES-256, Android Keystore)
- PDF: `android.graphics.pdf.PdfDocument`, geteilt über einen `FileProvider`
- minSdk 26 (Android 8.0), targetSdk 35

Upgrade-Pfad: Für Whisper-Qualität offline (und Audio-Datei-Import) kann
später whisper.cpp per JNI integriert werden (NDK-Build + Modell-Download
nötig).

## Bauen

```bat
cd BlitzdiktatAndroid
gradlew.bat assembleDebug
```

(Linux/macOS: `./gradlew assembleDebug`.) Der Gradle-Wrapper lädt Gradle
selbst herunter; nur JDK 17 und das Android SDK (`local.properties` mit
`sdk.dir=…`) müssen vorhanden sein. Oder das Projekt einfach in Android
Studio öffnen. Die APK liegt danach unter
`app/build/outputs/apk/debug/app-debug.apk`.

## Tests

```bat
gradlew.bat :app:testDebugUnitTest
```

Die JVM-Unit-Tests decken Prompt-Konstruktion, Verlaufs-Speicherung und die
Workflow-Definitionen ab. Der CI-Job `check-android` führt sie bei jedem
Push/PR aus und baut die Debug-APK.

## Release-Signing (optional)

Für signierte Release-Builds eine Datei `BlitzdiktatAndroid/key.properties`
anlegen (gitignored, niemals einchecken):

```properties
storeFile=blitzdiktat-release.jks
storePassword=…
keyAlias=blitzdiktat
keyPassword=…
```

Keystore erzeugen mit `keytool -genkeypair -v -keystore blitzdiktat-release.jks
-keyalg RSA -keysize 2048 -validity 10000 -alias blitzdiktat`, dann
`gradlew.bat assembleRelease`. Ohne `key.properties` entsteht eine
unsignierte Release-APK.

## Installieren (Sideload)

1. APK aufs Handy übertragen (USB, Cloud, Messenger an sich selbst …)
2. APK antippen → Installation aus unbekannten Quellen einmalig erlauben
3. App öffnen → Mikrofon-Berechtigung erteilen → optional API-Key eintragen
4. „Tastatur aktivieren" → Blitzdiktat-Tastatur einschalten
5. In beliebiger App: Tastatur-Symbol unten rechts → Blitzdiktat wählen → 🎙️
