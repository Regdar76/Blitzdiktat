# Security Policy

Blitzdiktat for Windows is experimental software.

It is provided as-is, without warranty, support guarantees, or production-readiness claims.

## Supported Versions

Only the current `main` branch is considered for security fixes.

## Reporting A Vulnerability

Please do not open a public issue with sensitive security details.

Use GitHub private vulnerability reporting for this repository.

If private vulnerability reporting is not available yet, open a minimal public issue titled `Security contact request` without technical details.

Do not include OpenAI API keys, access tokens, private recordings, or confidential transcripts in a report.

Include:

- what you found
- how to reproduce it
- what data or system access could be affected
- your suggested fix, if you have one

## Security Notes

- The app sends audio and text directly to OpenAI when you use online workflows.
- Your OpenAI API key is stored in the Windows Credential Manager.
- Temporary audio files may exist briefly in `%TEMP%` during processing; the app attempts to delete each recording when the workflow ends or is cancelled.
- Transcript and protocol files are saved in `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\` and are not encrypted.
- The paste mechanism simulates `Ctrl+V` via the Windows clipboard, which other processes can observe while the content is present.
- Local faster-whisper models are downloaded from Hugging Face on first use and cached in `%APPDATA%\Blitzdiktat\whisper_models\`. The app does not currently verify model checksums.

Do not use this preview for confidential or regulated data without your own review.
