# Sicherheitsnotizen

Privates Projekt — es gibt keinen öffentlichen Meldeprozess. Auffälligkeiten direkt als Issue im (privaten) Repository festhalten oder lokal fixen. Niemals API-Keys, Tokens, private Aufnahmen oder vertrauliche Transkripte in Issues, Commits oder Logs ablegen.

## Wo sensible Daten liegen

| | Windows | Android | macOS |
|---|---|---|---|
| OpenAI-Key | Windows Credential Manager | EncryptedSharedPreferences (AES-256, Android Keystore) | Keychain |
| Transkripte/PDFs | `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\` (unverschlüsselt, 14-Tage-Cleanup) | App-interner Speicher `files/Transkriptionen/` (14-Tage-Cleanup) | App Support (Cleanup-Service) |
| Vokabular | `%APPDATA%\Blitzdiktat\vocabulary.json` | `files/vocabulary.txt` + verschlüsselte Settings | — |

## Bekannte Eigenschaften, die man kennen sollte

- **OpenAI-Datenfluss:** LLM-Workflows (und auf Windows die optionale Online-Transkription) senden Text bzw. Audio direkt an OpenAI. Das automatische Vokabular-Lernen schickt Ergebnis-Texte zur Begriffs-Extraktion an OpenAI — beim rein lokalen Diktat wird es deshalb übersprungen.
- **Zwischenablage (Windows):** Das Einfügen simuliert `Ctrl+V` über die Zwischenablage; andere Prozesse können den Inhalt währenddessen lesen.
- **Temporäre Audiodateien (Windows):** liegen kurzzeitig in `%TEMP%`; die App löscht sie am Workflow-Ende.
- **Modell-Downloads:** Whisper-Modelle kommen von Hugging Face (Windows: `%APPDATA%\Blitzdiktat\whisper_models\`) bzw. über WhisperKit (macOS). Prüfsummen werden derzeit nicht verifiziert (siehe ROADMAP).
- **Android-Tastatur (IME):** verarbeitet Diktate wie die App; committete Texte landen im Eingabefeld der Ziel-App und unterliegen deren Handhabung.
- **Release-Signing (Android):** `key.properties` und Keystores sind gitignored und dürfen nie eingecheckt werden.

## Beim Entwickeln

- Vor jedem Commit prüfen, dass keine Secrets enthalten sind (`.github/secret-scan-patterns.txt` wird in der CI gegengeprüft).
- Keine Telemetrie und keine zusätzlichen externen Dienste einbauen.
- Vertrauliche oder regulierte Daten nur nach eigener Prüfung diktieren — die Apps sind Experimente, keine auditierte Software.
