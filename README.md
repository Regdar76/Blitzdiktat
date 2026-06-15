# ⚡ Blitzdiktat

Sprache rein. Text raus. — Diktier- und Schreibassistent für **Windows, Android und macOS**.

Blitzdiktat nimmt Sprache auf, transkribiert sie (lokal, wo immer möglich), verbessert den Text auf Wunsch per LLM und liefert das Ergebnis dorthin, wo es gebraucht wird: ins aktive Fenster, ins Eingabefeld oder in die Zwischenablage.

> Privates Projekt von Thorben Meier. Kein gehostetes Backend, kein eingebetteter API-Key — alle LLM-Workflows laufen mit eigenem OpenAI-Key (BYO-Key).

## Die Workflows

| Workflow | Funktion | Windows | Android | macOS |
|---|---|:-:|:-:|:-:|
| 🎙️ **Blitzdiktat** | Diktat → Text (lokal, ohne API-Key) | ✅ | ✅ | ✅ |
| ✨ **Blitzdiktat+** | Diktat → Text sprachlich verbessern | ✅ | ✅ | ✅ |
| 🔥 **Blitzdiktat $%&!** | Frust rein → ruhige, sachliche Nachricht raus | ✅ | ✅ | ✅ |
| 😊 **Blitzdiktat :)** | Text → mit passenden Emojis | ✅ | ✅ | ✅ |
| 📋 **Blitzdiktat Protokoll** | Besprechung → strukturiertes Protokoll (+ PDF) | ✅ | ✅ | — |

Alle Workflows außer dem reinen Blitzdiktat benötigen einen OpenAI-Key (`gpt-4o-mini` / `gpt-4o`, Modelle überschreibbar).

## Die drei Apps

| App | Plattform | Technik | Besonderheiten |
|---|---|---|---|
| **[Blitzdiktat für Windows](BlitzdiktatWin/README.md)** | Windows 10/11 | Python, customtkinter, pystray | System-Tray-App, globale Hotkeys (halten zum Diktieren), fügt direkt ins zuletzt aktive Fenster ein. Lokale Transkription via `faster-whisper` (tiny–large-v3). |
| **[Blitzdiktat für Android](BlitzdiktatAndroid/README.md)** | Android 8.0+ | Kotlin, Jetpack Compose | App mit Workflow-Karten **plus eigene Diktat-Tastatur (IME)** — Mikro-Taste in jeder App. Verlauf, Protokoll-PDF, Vokabular-Lernen. On-Device-Spracherkennung. |
| **[Blitztext für macOS](BlitztextMac/README.md)** | macOS | Swift, SwiftUI | Menüleisten-App mit globalen Hotkeys. Lokale Transkription via WhisperKit, Key in der Keychain. |

## Gemeinsame Prinzipien

- **Lokal zuerst:** Das reine Diktat läuft auf allen Plattformen ohne API-Key und ohne Cloud — Windows/macOS mit Whisper-Modellen auf dem Gerät, Android mit der On-Device-Spracherkennung des Systems.
- **Kein Backend:** Bei LLM-Workflows spricht das Gerät direkt mit der OpenAI-API. Es gibt keinen Zwischenserver.
- **Keys sicher verwahrt:** Windows Credential Manager / Android Keystore (EncryptedSharedPreferences) / macOS Keychain.
- **Ergebnisse lokal gespeichert:** Transkripte (und Protokoll-PDFs) landen im App-Speicher und werden nach 14 Tagen automatisch bereinigt.
- **Vokabular:** Eigennamen und Fachbegriffe lassen sich hinterlegen und werden automatisch dazugelernt, damit sie korrekt geschrieben werden (Windows + Android).

```
Lokale Transkription:   Gerät → Whisper/Geräte-Erkennung auf dem Gerät (kein Netzwerk)
Online-Transkription:   Gerät → OpenAI Audio Transcriptions API (nur Windows, optional)
Text-Workflows:         Gerät → OpenAI Chat Completions API
```

Vor dem Einsatz mit sensiblen Inhalten: [docs/privacy.md](docs/privacy.md) lesen.

## Projektstruktur

```
BlitzdiktatWin/      Windows-App (Python) — Tray, Hotkeys, faster-whisper
BlitzdiktatAndroid/  Android-App (Kotlin/Compose) + Diktat-Tastatur (IME)
BlitztextMac/        macOS-App "Blitztext" (Swift) — Menüleiste, WhisperKit
docs/                Setup, Datenschutz, lokale Modelle
.github/workflows/   CI: check-windows, check-android, build-macos
```

## Entwicklung

- Setup je Plattform: siehe jeweiliges README ([Windows](BlitzdiktatWin/README.md) · [Android](BlitzdiktatAndroid/README.md) · [macOS](BlitztextMac/README.md))
- Konventionen und Build-Befehle: [CONTRIBUTING.md](CONTRIBUTING.md)
- Geplante Arbeit: [ROADMAP.md](ROADMAP.md)
- Sicherheitsnotizen: [SECURITY.md](SECURITY.md)

## Lizenz

Code unter MIT-Lizenz, siehe [LICENSE](LICENSE). Namen, Logos und Icons sind davon ausgenommen, siehe [TRADEMARKS.md](TRADEMARKS.md).

Die **BlitztextMac**-App basiert ursprünglich auf der Blitztext-App von **Blackboat** ([blackboat.com](https://www.blackboat.com/)) — Originalprojekt: [github.com/cmagnussen/blitztext-app](https://github.com/cmagnussen/blitztext-app).

> Hinweis: Dieses Repository ist privat. Sollte es irgendwann veröffentlicht werden, vorher die Doku auf den Public-Kontext prüfen (Support-/Security-Prozesse, Branch-Schutz, Secret-Scanning).
