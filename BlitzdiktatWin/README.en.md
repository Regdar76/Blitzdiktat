# Blitzdiktat for Windows

> 🌐 [Deutsch](README.md) · **English**

Windows version of [Blitzdiktat](../README.en.md) — same idea, same workflows, a native Windows experience via the system tray.

## What it does

| Workflow | Shortcut (default) | Description |
|---|---|---|
| 🎙️ **Blitzdiktat** | `Ctrl+Shift+R` | Record speech → insert text |
| ✨ **Blitzdiktat+** | `Ctrl+Shift+T` | Record → transcribe → improve |
| 🔥 **Blitzdiktat $%&!** | `Ctrl+Shift+D` | Frustration in → calm message out |
| 😊 **Blitzdiktat :)** | `Ctrl+Shift+E` | Record text → add emojis |
| 📋 **Blitzdiktat Protokoll** | `Ctrl+Shift+P` | Record a meeting → generate structured minutes |

All shortcuts are freely configurable in the settings.

### Blitzdiktat Protokoll

Records a meeting, a discussion or a site meeting and automatically turns it into structured minutes in German — no matter which language was spoken. The minutes start with a summary that even outsiders can understand immediately, and below it contain the date, topic, participants, points discussed, decisions, open tasks with owners and deadlines, as well as — if mentioned during the conversation — the next appointment (insofar as it can be inferred from the content). The result is inserted into the most recently active window and additionally saved as a `.pdf`.

## Requirements

- Windows 11 (Windows 10 probably works too)
- Python 3.11 or newer
- For local transcription: `pip install faster-whisper`
- For text improvement, venting, emojis and minutes: an OpenAI API key with access to `gpt-4o-mini` and `gpt-4o`
- For online transcription: an OpenAI API key with access to `whisper-1`
- A microphone

## Installation

```bat
git clone https://github.com/Regdar76/Blitzdiktat.git
cd Blitzdiktat\BlitzdiktatWin
pip install -r requirements.txt
```

Recommended: use a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Starting

```bat
run.bat
```

Or directly:

```bat
python main.py
```

On first launch the main window opens automatically. Enter the OpenAI API key there or via "Settings" — it is stored securely in the Windows Credential Manager.

## Usage

**Shortcuts (hold mode):**
Hold the shortcut → speak → release → the text is transcribed and inserted into the most recently active window.

**Tray icon:**
- Left- or right-click → menu with all workflows and settings.
- The color shows the status: blue = ready, red = recording, yellow = processing, green = done.

**Main window:**
Click a workflow button → recording starts. Click again → recording stops and processing begins.

## Project structure

```
BlitzdiktatWin/
  main.py              Entry point
  app_state.py         Central app state
  services/
    credentials_service.py          Windows Credential Manager
    audio_recorder.py               Microphone recording (sounddevice)
    transcription_service.py        Dispatcher: local or online
    local_transcription_service.py  Offline transcription (faster-whisper)
    llm_service.py                  OpenAI Chat Completions
    hotkey_service.py               Global shortcuts (pynput)
    paste_service.py                Clipboard + Ctrl+V simulation
    transcript_store.py             Stores transcripts and minutes PDFs
  features/
    workflows/         Transcription, TextImprovement, DampfAblassen, EmojiText, Protokoll
    tray/              System tray icon (pystray)
    ui/                Main window + settings window (customtkinter)
  requirements.txt
  run.bat
```

## Local transcription

Offline transcription via `faster-whisper` is fully implemented and is the default mode. On first use the app automatically downloads the chosen model and stores it in:

```
%APPDATA%\Blitzdiktat\whisper_models\
```

Available models: tiny, base, small (default, recommended), medium, large-v3.

See [../docs/local-models.en.md](../docs/local-models.en.md) for details.

## Saved transcripts

All workflow outputs are automatically saved as a `.txt` file:

```
%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\
```

Minutes outputs are additionally saved as a formatted `.pdf` in the same folder. Files older than 14 days are cleaned up automatically.

## Privacy

```
Local transcription:    Your PC → faster-whisper on the device (no network)
Online transcription:   Your PC → OpenAI Audio Transcriptions API
Text rewriting:         Your PC → OpenAI Chat Completions API
```

No backend of our own. The API key is stored in the Windows Credential Manager.
Read [../docs/privacy.en.md](../docs/privacy.en.md) before using it with sensitive content.

## License

MIT — same as the main project. See [../LICENSE](../LICENSE).
