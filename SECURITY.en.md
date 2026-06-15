# Security Notes

> 🌐 [Deutsch](SECURITY.md) · **English**

Private project — there is no public reporting process. Note anything suspicious directly as an issue in the (private) repository or fix it locally. Never store API keys, tokens, private recordings, or confidential transcripts in issues, commits, or logs.

## Where sensitive data lives

| | Windows | Android | macOS |
|---|---|---|---|
| OpenAI key | Windows Credential Manager | EncryptedSharedPreferences (AES-256, Android Keystore) | Keychain |
| Transcripts/PDFs | `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\` (unencrypted, 14-day cleanup) | App-internal storage `files/Transkriptionen/` (14-day cleanup) | App Support (cleanup service) |
| Vocabulary | `%APPDATA%\Blitzdiktat\vocabulary.json` | `files/vocabulary.txt` + encrypted settings | — |

## Known characteristics you should be aware of

- **OpenAI data flow:** LLM workflows (and, on Windows, the optional online transcription) send text or audio directly to OpenAI. Automatic vocabulary learning sends result texts to OpenAI for term extraction — so it is skipped for purely local dictation.
- **Clipboard (Windows):** Pasting simulates `Ctrl+V` via the clipboard; other processes can read the content while it is there.
- **Temporary audio files (Windows):** are briefly stored in `%TEMP%`; the app deletes them at the end of the workflow.
- **Model downloads:** Whisper models come from Hugging Face (Windows: `%APPDATA%\Blitzdiktat\whisper_models\`) or via WhisperKit (macOS). Checksums are not currently verified (see ROADMAP).
- **Android keyboard (IME):** processes dictations like the app; committed texts end up in the target app's input field and are subject to its handling.
- **Release signing (Android):** `key.properties` and keystores are gitignored and must never be checked in.

## When developing

- Before every commit, check that no secrets are included (`.github/secret-scan-patterns.txt` is cross-checked in CI).
- Do not add telemetry or any additional external services.
- Only dictate confidential or regulated data after reviewing it yourself — the apps are experiments, not audited software.
