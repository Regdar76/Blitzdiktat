# Datenschutz-Notizen

> 🌐 **Deutsch** · [English](privacy.en.md)

Blitzdiktat hat auf keiner Plattform ein eigenes Backend. Bei Online-Workflows sendet das Gerät Daten direkt an OpenAI:

- Audio bei der Online-Transkription (nur Windows, optional)
- transkribierten oder eingegebenen Text bei den Schreib-Workflows
- hinterlegte Begriffe (Vokabular) und Prompt-Kontext, falls konfiguriert
- Ergebnis-Texte für das automatische Vokabular-Lernen (Begriffs-Extraktion); beim rein lokalen Diktat wird das übersprungen — dort verlässt nichts das Gerät

Nur die **Transkription** kann lokal laufen (Windows: `faster-whisper`, Android: Geräte-Spracherkennung, macOS: WhisperKit). Jeder Workflow, der Text umschreibt oder verbessert, braucht OpenAI und kann nicht vollständig offline laufen.

API-Nutzung, Kosten und Datenhandling laufen über das eigene OpenAI-Konto.

## Lokale Daten

**Windows**

- OpenAI-Key im Windows Credential Manager
- Einstellungen in `%APPDATA%\Blitzdiktat\settings.json` (Klartext-JSON — keine Geheimnisse in Prompts/Kontext-Felder schreiben)
- Whisper-Modelle in `%APPDATA%\Blitzdiktat\whisper_models\`
- temporäre Audiodateien in `%TEMP%` während der Verarbeitung (werden am Workflow-Ende gelöscht)
- Transkripte (`.txt`) und Protokoll-PDFs in `%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\`, automatische Bereinigung nach 14 Tagen
- Gelerntes Vokabular in `%APPDATA%\Blitzdiktat\vocabulary.json`

**Android**

- OpenAI-Key und Einstellungen in `EncryptedSharedPreferences` (AES-256, Schlüssel im Android Keystore)
- Transkripte/PDFs im app-internen Speicher (`files/Transkriptionen/`), Bereinigung nach 14 Tagen
- Gelerntes Vokabular in `files/vocabulary.txt`
- Die Diktat-Tastatur schreibt Ergebnisse direkt ins Eingabefeld der Ziel-App — ab dort gelten deren Regeln

**macOS**

- OpenAI-Key in der Keychain
- WhisperKit-Modelle und App-Daten im Application-Support-Verzeichnis, mit Aufräum-Service

## Zwischenablage (Windows)

Workflow-Ergebnisse laufen über die Zwischenablage (simuliertes `Ctrl+V`). Solange der Inhalt dort liegt, können andere Prozesse und Clipboard-Manager ihn sehen oder aufbewahren.

## Sensible Inhalte

Vertrauliche oder regulierte Inhalte nur diktieren, wenn Code, OpenAI-Einstellungen und die eigenen rechtlichen Anforderungen geprüft sind — die Apps sind Experimente, keine auditierte Software.
