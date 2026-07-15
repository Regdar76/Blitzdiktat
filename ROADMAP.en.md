# Roadmap

> 🌐 [Deutsch](ROADMAP.md) · **English**

Working list for further development — no commitments, just direction.

## Current state

Current versions: see [Releases](https://github.com/Regdar76/Blitzdiktat/releases).

| | Windows | Android | macOS (Blitztext) |
|---|---|---|---|
| Local dictation | ✅ faster-whisper | ✅ device recognition | ✅ WhisperKit |
| LLM workflows (+, $%&!, :)) | ✅ | ✅ | ✅ |
| Protokoll (+ PDF) | ✅ | ✅ | — |
| History (14 days) | ✅ | ✅ | partial |
| Vocabulary (manual + learned) | ✅ | ✅ | — |
| Custom prompts/names per workflow | ✅ | ✅ | — |
| Tests + CI | ✅ pytest | ✅ JUnit | build job |

## Windows

- Make the first launch clearer, especially feedback during the model download
- Improve credential setup, validation, and recovery
- Sharpen provider boundaries so OpenAI and local transcription are cleanly interchangeable
- Local text rewriting so the writing workflows can also run offline
- Protokoll: speaker recognition, automatic language detection, custom templates
- Checksum verification for downloaded Whisper models
- Installer maintenance (Inno Setup is included, releases as needed)

## Android

- **whisper.cpp via JNI** for true Whisper quality offline — this also solves:
  - vocabulary for pure dictation (term list as Whisper prompt)
  - audio file import for the Protokoll (so far text files only)
  - gapless Protokoll recording (SpeechRecognizer loses short snippets when restarting a segment)
- Strings to `strings.xml`, a clean dark theme instead of hardcoded colors
- Replace `security-crypto` (deprecated) with a custom Keystore solution
- Release builds with minify/ProGuard, once tested on devices

## macOS

- Catch up the Protokoll workflow (including PDF export)
- Bring history and vocabulary up to the Windows/Android level
- Custom prompts/names per workflow

## Deliberately not planned

- Hosted backend, accounts, sync, or teams
- Embedded API key in distributed apps
