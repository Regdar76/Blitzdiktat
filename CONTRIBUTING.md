# Contributing

Thanks for taking a look at Blitzdiktat for Windows.

This repository is intentionally a preview. Contributions should make it easier to learn from, build, fork, or safely extend.

## Good First Contributions

- improve setup or install instructions
- fix confusing UI text
- improve error messages
- add tests around prompt construction or quality filters
- document local model experiments
- simplify the setup flow

## Before Opening A Pull Request

Please include:

- what changed
- why it changed
- how you tested it
- whether you used AI-assisted coding tools

Keep changes small when possible. Avoid unrelated cleanup in the same PR.

## Local Setup

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Security And Privacy

- Never commit API keys, tokens, private audio, or confidential transcripts.
- Avoid adding telemetry, hosted services, or external dependencies without a clear issue first.
- Call out privacy-impacting changes in the pull request description.
- Keep the preview honest: do not describe remote OpenAI workflows as offline or local.

## Project Boundaries

This preview currently does not include:

- a hosted backend
- packaged installer releases
- bundled local model files
- local text rewriting (rewriting still requires OpenAI)

Those can be discussed in issues, but please keep PRs focused on the current Windows preview unless a maintainer agrees on a larger direction first.
