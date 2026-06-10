# Roadmap

This is a preview roadmap, not a promise.

## Current Scope

- Windows system tray app
- local recording and hotkeys
- offline transcription via `faster-whisper` (default)
- direct OpenAI API calls with a user-provided API key for online transcription
- transcription, rewriting, calm-message, emoji, and protocol workflows
- automatic saving of transcripts as `.txt` and protocols as `.pdf`
- no hosted backend

## Next Useful Work

- Make first-run setup clearer, especially model download feedback.
- Improve credential setup, validation, and recovery UX.
- Add a small automated test layer around prompt construction and text quality filters.
- Add provider boundaries so OpenAI and local transcription can be swapped more cleanly.
- Add local text rewriting so the rewriting workflows can run fully offline.
- Improve the Protokoll workflow: speaker detection, language auto-detection, custom templates.
- Add a packaged Windows installer for non-developer users.
- Add stronger supply-chain checks around downloaded local speech models.

## Not In Scope Yet

- Production support.
- Accounts, sync, teams, or hosted infrastructure.
- Claims that all workflows are offline or privacy-complete (rewriting still uses OpenAI).
- Other platforms.
- Bundled local models.
