# Local Models

> 🌐 [Deutsch](local-models.md) · **English**

Transcription runs locally — no API key, audio never leaves the device:

- **Windows:** `faster-whisper` (CTranslate2 backend)
- **macOS:** WhisperKit
- **Android:** the system's on-device speech recognition (no Whisper; whisper.cpp is on the [Roadmap](../ROADMAP.en.md))

## Available Whisper models (Windows)

| Model | Size | Note |
|---|---|---|
| tiny | ~75 MB | Very fast, less accurate |
| base | ~150 MB | Fast |
| small | ~500 MB | Good compromise — **recommended default** |
| medium | ~1.5 GB | More accurate |
| large-v3 | ~3 GB | Best quality |

All models are multilingual (German, English and many other languages).

## Model cache

```
%APPDATA%\Blitzdiktat\whisper_models\
```

The folder is created automatically. Models are downloaded from Hugging Face on first use — they are not bundled with the app.

## Choosing a model

**Settings → Transcription** → select the model from the dropdown. The selected model downloads on first use; after that it comes straight from the cache. For most cases **small** is the right choice; use **tiny**/**base** when storage is tight or the connection is slow.

## Installing faster-whisper

```bat
pip install faster-whisper
```

Then restart the app. If the package is missing, the app shows a warning and offers online transcription with an OpenAI key as a fallback.

## Notes

- The first run after switching models is slower (download + initial load).
- By default models run on the CPU with `int8` quantization — they work without a GPU.
- Local transcription avoids sending audio to external services; the writing step of the LLM workflows still uses OpenAI.
- Model checksums are currently not verified after download ([Roadmap](../ROADMAP.en.md)).
