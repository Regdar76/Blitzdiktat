# Setup

This guide is for people who want to run and inspect the preview themselves.

## 1. Requirements

- Windows 11 (Windows 10 likely works too)
- Python 3.11 or newer
- A microphone
- For local transcription: `faster-whisper` (see step 3)
- For online transcription and all rewriting workflows: an OpenAI API key

## 2. Clone And Install

```bat

cd blitztext-app\BlitzdiktatWin
```

Recommended: use a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Or install directly:

```bat
pip install -r requirements.txt
```

## 3. Local Transcription (Recommended)

Local transcription runs fully offline via `faster-whisper`. It is the default mode.

If `faster-whisper` is not yet installed, add it:

```bat
pip install faster-whisper
```

On first use, the app downloads the selected Whisper model automatically from Hugging Face and caches it in `%APPDATA%\Blitzdiktat\whisper_models\`. The default model is **Small (~500 MB)**. Download happens once in the background.

See [local-models.md](local-models.md) for all available models and sizes.

## 4. Configure OpenAI For Online And Rewriting Workflows

Open the app settings and paste your own OpenAI API key if you want:

- online transcription (uses `whisper-1`)
- text improvement (uses `gpt-4o-mini`)
- calm-message workflow (uses `gpt-4o`)
- emoji workflow (uses `gpt-4o-mini`)
- protocol workflow (uses `gpt-4o-mini` for transcription, `gpt-4o` for the protocol)

You are responsible for API access, billing, and data handling in your own OpenAI account.

Never commit your API key into this repository, issues, logs, or screenshots.

You can skip this step entirely if you only want to use local transcription without rewriting.

## 5. Run

```bat
run.bat
```

Or directly:

```bat
python main.py
```

On first launch the main window opens automatically. Enter your API key there or via Settings — it is stored in the Windows Credential Manager.

## 6. Windows Microphone Permission

If the app cannot access the microphone, check Windows microphone privacy settings:

**Settings → Privacy & Security → Microphone → Allow desktop apps to access your microphone**

## Troubleshooting

- **`faster-whisper` not found**: run `pip install faster-whisper` and restart the app.
- **Model download is slow**: the Small model is ~500 MB and downloads once on first use. Use Tiny (~75 MB) for faster startup.
- **Online transcription fails immediately**: check whether the API key is present and valid in settings.
- **Paste does not work**: confirm that the app process is not blocked by clipboard access restrictions. The paste mechanism simulates `Ctrl+V`.
- **Audio is missing or silent**: check microphone permission in Windows settings and confirm the correct device is selected in app settings.
- **OpenAI errors**: verify model access and account billing status.
- **`hotkey_protokoll` setting not saved**: if you have an existing `settings.json` from an older version, add `"hotkey_protokoll": "ctrl+shift+p"` manually or delete the file to reset to defaults.
