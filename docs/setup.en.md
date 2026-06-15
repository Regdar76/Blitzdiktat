# Setup (Windows)

> 🌐 [Deutsch](setup.md) · **English**

Setting up the Windows app on a new machine. For Android and macOS see the respective README ([Android](../BlitzdiktatAndroid/README.en.md) · [macOS](../BlitztextMac/README.en.md)).

## 1. Requirements

- Windows 11 (Windows 10 probably works too)
- Python 3.11 or newer
- A microphone
- For local transcription: `faster-whisper` (step 3)
- For online transcription and all writing workflows: an OpenAI API key

## 2. Clone and install

```bat
git clone https://github.com/Regdar76/Blitzdiktat.git
cd Blitzdiktat\BlitzdiktatWin
```

Recommended: a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Local transcription (recommended)

Local transcription runs fully offline via `faster-whisper` and is the default mode.

```bat
pip install faster-whisper
```

On first use the app automatically downloads the selected Whisper model from Hugging Face and stores it in `%APPDATA%\Blitzdiktat\whisper_models\`. The default is **Small (~500 MB)** — the download happens once in the background.

All models and sizes: [local-models.en.md](local-models.en.md).

## 4. OpenAI for online and writing workflows

Enter your own OpenAI API key in the app settings, if desired:

- online transcription (`whisper-1`)
- text improvement (`gpt-4o-mini`)
- venting (`gpt-4o`)
- emojis (`gpt-4o-mini`)
- minutes (`gpt-4o`)

API access, billing and data handling go through your own OpenAI account. Never put the key into the repository, into issues, logs or screenshots.

If you only want to dictate locally, you can skip this step entirely.

## 5. Starting

```bat
run.bat
```

Or directly: `python main.py`. On first launch the main window opens automatically; the key moves into the Windows Credential Manager.

## 6. Microphone permission

If the app cannot access the microphone:

**Settings → Privacy & security → Microphone → allow desktop apps access**

## Troubleshooting

- **`faster-whisper` not found:** `pip install faster-whisper`, then restart the app.
- **Model download slow:** Small (~500 MB) downloads once; for a faster start choose Tiny (~75 MB).
- **Online transcription fails immediately:** is the key present and valid in the settings?
- **Pasting does not work:** the mechanism simulates `Ctrl+V` — check whether something is blocking clipboard access.
- **No/quiet audio:** check microphone permission and device selection in the app settings.
- **OpenAI errors:** check model access and billing status in your OpenAI account.
- **`hotkey_protokoll` is not saved:** with a `settings.json` from an older version, manually add `"hotkey_protokoll": "ctrl+shift+p"` or delete the file (reset to defaults).
