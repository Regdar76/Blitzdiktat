# Open Source Preflight

Use this checklist before making the repository public.

## P0 Before Public

- Confirm the app starts with `python main.py` from a clean install.
- Run a secret scan across the working tree and commit history.
- Confirm there are no private URLs, hosted backend credentials, internal docs, or old project references.
- Keep the repository private until another maintainer has reviewed the first public commit.
- Confirm the root `LICENSE`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `SUPPORT.md` are present.
- Make the preview status explicit: experimental, bring your own OpenAI API key, no hosted backend, no warranty.
- Enable GitHub private vulnerability reporting, secret scanning, and push protection before switching the repo public.
- Enable Dependabot alerts.
- Protect `main` with pull requests, at least one review, and required CI checks.
- Keep GitHub Actions permissions read-only by default.

## P1 Soon After Public

- Enable private vulnerability reporting.
- Decide whether Issues alone are enough or whether Discussions should be enabled for questions.
- Add repository topics such as `windows`, `python`, `speech-to-text`, `openai`, `faster-whisper`, and `system-tray`.
- Add a lightweight release process only after a packaged installer is ready.
- Add basic tests once provider boundaries are extracted.

## P2 Later

- Add CODEOWNERS if multiple maintainers become active.
- Add model checksum verification after download.
- Consider CodeQL once the repo has enough surface area to justify scheduled scans.
- Add a packaged Windows installer for non-developer users.
