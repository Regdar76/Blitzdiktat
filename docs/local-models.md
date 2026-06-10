# Local Models

Blitzdiktat can run transcription locally via `faster-whisper` (CTranslate2 backend). No API key is needed for transcription in local mode. Models are downloaded automatically from Hugging Face on first use and cached locally.

## Available Models

| Model | Size | Notes |
|---|---|---|
| tiny | ~75 MB | Very fast, less accurate |
| base | ~150 MB | Fast |
| small | ~500 MB | Good balance — **recommended default** |
| medium | ~1.5 GB | More accurate |
| large-v3 | ~3 GB | Best quality |

All models are multilingual and support German, English, and many other languages.

## Model Cache Location

```
%APPDATA%\Blitzdiktat\whisper_models\
```

The app creates this folder automatically. Models are downloaded on first use — they do not ship with the app.

## Selecting A Model

Open the app settings, go to **Einstellungen → Transkription**, and choose a model from the dropdown. The selected model is downloaded on first use. Subsequent runs load the cached model directly.

The **small** model is recommended for most use cases. Use **tiny** or **base** if download speed or memory usage is a concern.

## Install faster-whisper

If `faster-whisper` is not yet installed:

```bat
pip install faster-whisper
```

Then restart the app. If the package is missing, the app shows a warning and falls back to prompting for an OpenAI API key.

## Notes

- First use after selecting a new model can be slower because the model downloads and loads for the first time.
- Models run on CPU with `int8` quantization by default. This works on all Windows machines without a GPU.
- Local transcription avoids sending audio to any external service for the Blitzdiktat, Blitzdiktat+, Blitzdiktat $%&!, Blitzdiktat :), and Blitzdiktat Protokoll workflows — but the rewriting step in those workflows still uses OpenAI.
- The app does not currently verify model checksums after download. Only use the app on machines you trust.
