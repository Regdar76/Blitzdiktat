# Privacy Notes

> 🌐 [Deutsch](privacy.md) · **English**

Blitzdiktat has no backend of its own on any platform. For online workflows, the device sends data directly to OpenAI:

- audio during online transcription (Windows only, optional)
- transcribed or entered text in the writing workflows
- stored terms (vocabulary) and prompt context, if configured
- result texts for automatic vocabulary learning (term extraction); with purely local dictation this is skipped — nothing leaves the device there

Only **transcription** can run locally (Windows: `faster-whisper`, Android: device speech recognition, macOS: WhisperKit). Any workflow that rewrites or improves text requires OpenAI and cannot run fully offline.

API usage, costs and data handling go through your own OpenAI account.

## Local data

**Windows**

- OpenAI key in the Windows Credential Manager
- settings in `%APPDATA%\Blitzdiktat\settings.json` (plaintext JSON — do not write any secrets into prompt/context fields)
- Whisper models in `%APPDATA%\Blitzdiktat\whisper_models\`
- temporary audio files in `%TEMP%` during processing (deleted at the end of the workflow)
- transcripts (`.txt`) and minutes PDFs in `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\`, automatic cleanup after 14 days
- learned vocabulary in `%APPDATA%\Blitzdiktat\vocabulary.json`

**Android**

- OpenAI key and settings in `EncryptedSharedPreferences` (AES-256, key in the Android Keystore)
- transcripts/PDFs in app-internal storage (`files/Transkriptionen/`), cleanup after 14 days
- learned vocabulary in `files/vocabulary.txt`
- the dictation keyboard writes results directly into the target app's input field — from there its rules apply

**macOS**

- OpenAI key in the Keychain
- WhisperKit models and app data in the Application Support directory, with a cleanup service

## Clipboard (Windows)

Workflow results go through the clipboard (simulated `Ctrl+V`). As long as the content sits there, other processes and clipboard managers can see or retain it.

## Sensitive content

Only dictate confidential or regulated content once you have reviewed the code, the OpenAI settings and your own legal requirements — the apps are experiments, not audited software.
