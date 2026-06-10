# Blitzdiktat for Windows

Blitzdiktat is an experimental open-source Windows app for turning speech into text — a system tray app that stays ready in the background.

It is intentionally small and unfinished. The goal is to make a real AI workflow visible and hackable: press a hotkey, speak, get text back, optionally rewrite it, and paste it into the app you were using.

This is a learning and experimentation project, not a polished product.

> Preview status: bring your own OpenAI API key for online workflows, or run fully offline with the built-in local transcription. No hosted backend, no warranty, no support guarantee.

## What It Does

| Workflow | Hotkey (default) | Description |
|---|---|---|
| 🎙️ **Blitzdiktat** | `Ctrl+Shift+R` | Record speech → paste as text |
| ✨ **Blitzdiktat+** | `Ctrl+Shift+T` | Record → transcribe → improve writing |
| 🔥 **Blitzdiktat $%&!** | `Ctrl+Shift+D` | Frustrated speech → calmer message |
| 😊 **Blitzdiktat :)** | `Ctrl+Shift+E` | Dictate text → add fitting emojis |
| 📋 **Blitzdiktat Protokoll** | `Ctrl+Shift+P` | Record a meeting → get a structured protocol |

All hotkeys are freely configurable in settings.

## Important Preview Notes

- Windows only. (Windows 11 recommended, Windows 10 likely works too.)
- Local transcription via `faster-whisper` works out of the box — no API key needed for transcription.
- For text improvement, calm-message, emoji, and protocol workflows: bring your own OpenAI API key.
- No hosted Blitzdiktat backend is included or provided.
- Not production ready.
- No warranty and no support guarantee.

You are welcome to use, fork, adapt, and share this project under the license terms.

The intent is not to ship a one-click finished app. The intent is to make a real AI workflow understandable: clone it, run it, read the code, change it, break it, fix it, and suggest improvements.

## Requirements

- Windows 11 (Windows 10 likely works too)
- Python 3.11 or newer
- For local transcription: `pip install faster-whisper` (the app will prompt you if it is missing)
- For text improvement, calm-message, emoji, and protocol workflows: an OpenAI API key with access to `gpt-4o-mini` and `gpt-4o`
- For online transcription: an OpenAI API key with access to `whisper-1`
- A microphone

## Setup

```bat
git clone https://github.com/cmagnussen/blitztext-app.git
cd blitztext-app\BlitzdiktatWin
pip install -r requirements.txt
```

Recommended: use a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bat
run.bat
```

Or directly:

```bat
python main.py
```

On first launch the main window opens automatically. Enter your OpenAI API key there or via Settings — it is stored securely in the Windows Credential Manager.

For a more detailed walkthrough, see [docs/setup.md](docs/setup.md).

## How To Use

**Hotkeys (hold mode):**
Hold the hotkey → speak → release → text is transcribed and pasted into the last active window.

**Tray icon:**
- Left-click or right-click → menu with all workflows and settings.
- Icon color shows status: blue = ready, red = recording, yellow = processing, green = done.

**Main window:**
Click a workflow button → recording starts. Click again → recording stops and processing begins.

## Permissions

Blitzdiktat needs:

- **Microphone**: to record your voice.
- **Clipboard access**: to paste the result via simulated `Ctrl+V`.

## Data Flow

The app has no custom backend.

```
Local transcription:  Your PC → faster-whisper on device (no network)
Online transcription: Your PC → OpenAI Audio Transcriptions API
Text rewriting:       Your PC → OpenAI Chat Completions API
```

Your OpenAI API key is stored in the Windows Credential Manager.

Read [docs/privacy.md](docs/privacy.md) before using the preview with sensitive content.

## Project Structure

```
BlitzdiktatWin/
  main.py              Entry point
  app_state.py         Central app state
  services/
    credentials_service.py        Windows Credential Manager
    audio_recorder.py             Microphone recording (sounddevice)
    transcription_service.py      Dispatches to local or online transcription
    local_transcription_service.py  faster-whisper offline transcription
    llm_service.py                OpenAI Chat Completions
    hotkey_service.py             Global hotkeys (pynput)
    paste_service.py              Clipboard + Ctrl+V simulation
    transcript_store.py           Saves transcripts and protocol PDFs locally
  features/
    workflows/         Transcription, TextImprovement, DampfAblassen, EmojiText, Protokoll
    tray/              System tray icon (pystray)
    ui/                Main window + settings window (customtkinter)
  requirements.txt
  run.bat
docs/             Setup, privacy, roadmap, local models
```

## Local Transcription

Offline transcription via `faster-whisper` is fully implemented and is the default mode. The app downloads the selected model automatically on first use and caches it in:

```
%APPDATA%\Blitzdiktat\whisper_models\
```

Available models: tiny, base, small (default, recommended), medium, large-v3.

See [docs/local-models.md](docs/local-models.md) for details.

## Saved Transcripts

All workflow outputs are saved automatically as `.txt` files in:

```
%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\
```

Protocol outputs are additionally saved as formatted `.pdf` files in the same folder. Files older than 14 days are cleaned up automatically.

## Contributing

Contributions are welcome, especially if they make the preview easier to build, understand, or fork.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Support And Roadmap

This preview has no formal support promise. See [SUPPORT.md](SUPPORT.md) for how to ask for help without sharing secrets.

The current direction is documented in [ROADMAP.md](ROADMAP.md).

## License

Code is released under the MIT License. See [LICENSE](LICENSE).

Project names, logos, and app icons are not automatically granted as trademarks or brand assets. See [TRADEMARKS.md](TRADEMARKS.md).
