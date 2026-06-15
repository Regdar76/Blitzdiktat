# ⚡ Blitzdiktat

> 🌐 [Deutsch](README.md) · **English**

Speech in. Text out. — Dictation and writing assistant for **Windows, Android and macOS**.

Blitzdiktat records speech, transcribes it (locally wherever possible), refines the text on demand via an LLM, and delivers the result wherever it's needed: into the active window, into the input field, or onto the clipboard.

> Private project by Thorben Meier. No hosted backend, no embedded API key — all LLM workflows run with your own OpenAI key (BYO key).

## The Workflows

| Workflow | Function | Windows | Android | macOS |
|---|---|:-:|:-:|:-:|
| 🎙️ **Blitzdiktat** | Dictation → text (local, no API key) | ✅ | ✅ | ✅ |
| ✨ **Blitzdiktat+** | Dictation → linguistically refined text | ✅ | ✅ | ✅ |
| 🔥 **Blitzdiktat $%&!** | Frustration in → calm, factual message out | ✅ | ✅ | ✅ |
| 😊 **Blitzdiktat :)** | Text → with fitting emojis | ✅ | ✅ | ✅ |
| 📋 **Blitzdiktat Protokoll** | Meeting → structured minutes (+ PDF) | ✅ | ✅ | — |

All workflows except plain Blitzdiktat require an OpenAI key (`gpt-4o-mini` / `gpt-4o`, models can be overridden).

## The Three Apps

| App | Platform | Technology | Highlights |
|---|---|---|---|
| **[Blitzdiktat for Windows](BlitzdiktatWin/README.en.md)** | Windows 10/11 | Python, customtkinter, pystray | System tray app, global hotkeys (hold to dictate), inserts directly into the most recently active window. Local transcription via `faster-whisper` (tiny–large-v3). |
| **[Blitzdiktat for Android](BlitzdiktatAndroid/README.en.md)** | Android 8.0+ | Kotlin, Jetpack Compose | App with workflow cards **plus its own dictation keyboard (IME)** — a mic key in every app. History, minutes PDF, vocabulary learning. On-device speech recognition. |
| **[Blitztext for macOS](BlitztextMac/README.en.md)** | macOS | Swift, SwiftUI | Menu bar app with global hotkeys. Local transcription via WhisperKit, key stored in the Keychain. |

## Shared Principles

- **Local first:** Plain dictation runs on all platforms without an API key and without the cloud — Windows/macOS with Whisper models on the device, Android with the system's on-device speech recognition.
- **No backend:** For LLM workflows, the device talks directly to the OpenAI API. There is no intermediate server.
- **Keys kept securely:** Windows Credential Manager / Android Keystore (EncryptedSharedPreferences) / macOS Keychain.
- **Results stored locally:** Transcripts (and minutes PDFs) end up in the app's storage and are automatically cleaned up after 14 days.
- **Vocabulary:** Proper names and technical terms can be stored and are learned automatically so they're spelled correctly (Windows + Android).

```
Local transcription:    Device → Whisper/device recognition on the device (no network)
Online transcription:   Device → OpenAI Audio Transcriptions API (Windows only, optional)
Text workflows:         Device → OpenAI Chat Completions API
```

Before using with sensitive content: read [docs/privacy.md](docs/privacy.en.md).

## Project Structure

```
BlitzdiktatWin/      Windows app (Python) — tray, hotkeys, faster-whisper
BlitzdiktatAndroid/  Android app (Kotlin/Compose) + dictation keyboard (IME)
BlitztextMac/        macOS app "Blitztext" (Swift) — menu bar, WhisperKit
docs/                Setup, privacy, local models
.github/workflows/   CI: check-windows, check-android, build-macos
```

## Development

- Setup per platform: see the respective README ([Windows](BlitzdiktatWin/README.en.md) · [Android](BlitzdiktatAndroid/README.en.md) · [macOS](BlitztextMac/README.en.md))
- Conventions and build commands: [CONTRIBUTING.md](CONTRIBUTING.en.md)
- Planned work: [ROADMAP.md](ROADMAP.en.md)
- Security notes: [SECURITY.md](SECURITY.en.md)

## License

Code under the MIT license, see [LICENSE](LICENSE). Names, logos and icons are excluded from it, see [TRADEMARKS.md](TRADEMARKS.en.md).

The **BlitztextMac** app is originally based on the Blitztext app by **Blackboat** ([blackboat.com](https://www.blackboat.com/)) — original project: [github.com/cmagnussen/blitztext-app](https://github.com/cmagnussen/blitztext-app).

> Note: This repository is public. Before every push, verify that no secrets (API keys, signing keys) or sensitive data are included — see [SECURITY.md](SECURITY.en.md).
