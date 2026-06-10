# Support

Blitzdiktat for Windows is an experimental preview. There is no service-level agreement, paid support channel, or guarantee that issues will be fixed.

## Before Asking For Help

- Make sure you can start the app with `run.bat` or `python main.py`.
- Check that your OpenAI API key is entered in the app settings (required for text improvement, calm-message, emoji, and protocol workflows).
- For local transcription: confirm that `faster-whisper` is installed (`pip install faster-whisper`).
- Confirm that Windows microphone permission is granted for the Python process.
- Read [docs/privacy.md](docs/privacy.md) before testing with sensitive content.

## Where To Ask

Use GitHub Issues for reproducible bugs and focused feature ideas.

Please do not post:

- OpenAI API keys
- access tokens
- private audio recordings
- confidential transcripts
- screenshots that show sensitive content

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
