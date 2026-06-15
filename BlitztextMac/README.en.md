# Blitztext for macOS

> 🌐 [Deutsch](README.md) · **English**

macOS version of [Blitzdiktat](../README.en.md) — same idea, same workflows, as a native menu bar app.

## What it does

| Workflow | Description |
|---|---|
| 🎙️ **Blitzdiktat** | Record speech → insert text (local, no API key) |
| ✨ **Blitzdiktat+** | Record → transcribe → improve the wording |
| 🔥 **Blitzdiktat $%&!** | Frustration in → calm, factual message out |
| 😊 **Blitzdiktat :)** | Record text → add fitting emojis |

The Protokoll workflow is not yet implemented on the Mac (see [ROADMAP.en.md](../ROADMAP.en.md)).

## Technology

- Swift + SwiftUI, menu bar app (popover, ~340 pt)
- Global hotkeys via a custom `HotkeyService` (Accessibility permission required)
- Local transcription via **WhisperKit** — models are downloaded on demand
  and run on the device, no API key needed
- LLM workflows: OpenAI Chat Completions, models like on the other platforms
- API key storage: macOS **Keychain**
- Launch at login optional (`LaunchAtLoginService`)
- Cleanup logic for old recordings/transcripts (`BlitztextCleanupService`)

## Building

Requirements: Xcode (16+), [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`).

```bash
./build.sh            # Release build
./build.sh --debug    # Debug build
```

The script generates the Xcode project from [project.yml](project.yml) and builds `Blitztext.app`. The CI job `build-macos` does the same on every push.

## Permissions

- **Microphone** — for recording
- **Accessibility** — for global hotkeys and inserting into the active program

## License

MIT — like the main project, see [../LICENSE](../LICENSE).

This app is originally based on the Blitztext app by **Blackboat** ([blackboat.com](https://www.blackboat.com/)) — original project: [github.com/cmagnussen/blitztext-app](https://github.com/cmagnussen/blitztext-app).
