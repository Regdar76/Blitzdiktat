# Privacy Notes

Blitzdiktat for Windows does not include a hosted backend.

When you use online workflows, your PC sends data directly to OpenAI:

- audio recordings for online transcription
- transcribed or typed text for rewriting workflows
- custom terms and prompt context if you configured them

When the transcription backend is set to **local**, transcription runs on your PC via `faster-whisper` and does not send audio to OpenAI. Rewriting workflows (Blitzdiktat+, Blitzdiktat $%&!, Blitzdiktat :), Blitzdiktat Protokoll) still require OpenAI and cannot run fully offline.

You are responsible for your OpenAI account, API usage, costs, and data handling.

## Local Data

The app stores:

- your OpenAI API key in the Windows Credential Manager
- workflow settings in `%APPDATA%\Blitzdiktat\settings.json`
- faster-whisper model files in `%APPDATA%\Blitzdiktat\whisper_models\`
- temporary audio files in `%TEMP%` while a transcription is being processed; the app attempts to delete each recording when the workflow ends or is cancelled
- transcript files (`.txt`) and protocol PDFs (`.pdf`) in `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\`; files older than 14 days are cleaned up automatically

Workflow output is placed on the Windows clipboard so it can be pasted into another app. The clipboard content is visible to other processes while it is present on the clipboard. Clipboard managers or other apps may observe or retain this content.

Settings such as custom prompts, custom terms, and context are stored in `settings.json` as plain JSON. Do not put secrets into those fields.

## Offline Scope

Only transcription can run locally. Any workflow that rewrites, improves, or transforms text still sends data to OpenAI.

## Sensitive Content

Do not use this preview with confidential, regulated, or highly sensitive content unless you have reviewed the code, your OpenAI settings, and your legal and privacy requirements.
