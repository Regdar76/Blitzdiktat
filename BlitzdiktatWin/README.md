# Blitzdiktat für Windows

> 🌐 **Deutsch** · [English](README.en.md)

Windows-Version von [Blitzdiktat](../README.md) — gleiche Idee, gleiche Workflows, native Windows-Erfahrung über das System-Tray.

## Was es macht

| Workflow | Tastenkürzel (Standard) | Beschreibung |
|---|---|---|
| 🎙️ **Blitzdiktat** | `Ctrl+Shift+R` | Sprache aufnehmen → Text einfügen |
| ✨ **Blitzdiktat+** | `Ctrl+Shift+T` | Aufnehmen → transkribieren → verbessern |
| 🔥 **Blitzdiktat $%&!** | `Ctrl+Shift+D` | Frust rein → ruhige Nachricht raus |
| 😊 **Blitzdiktat :)** | `Ctrl+Shift+E` | Text aufnehmen → Emojis hinzufügen |
| 📋 **Blitzdiktat Protokoll** | `Ctrl+Shift+P` | Besprechung aufnehmen → strukturiertes Protokoll erzeugen |

Alle Tastenkürzel sind in den Einstellungen frei konfigurierbar.

### Blitzdiktat Protokoll

Nimmt eine Besprechung, ein Meeting oder eine Baubesprechung auf und erstellt daraus automatisch ein strukturiertes Protokoll auf Deutsch — egal in welcher Sprache gesprochen wurde. Das Protokoll beginnt mit einer Zusammenfassung, die auch Außenstehende sofort verstehen, und enthält darunter Datum, Thema, Teilnehmer, besprochene Punkte, Entscheidungen, offene Aufgaben mit Verantwortlichen und Deadlines sowie — falls im Gespräch genannt — den nächsten Termin (soweit aus dem Inhalt erkennbar). Das Ergebnis wird in das zuletzt aktive Fenster eingefügt und zusätzlich als `.pdf` gespeichert.

## Voraussetzungen

- Windows 11 (Windows 10 funktioniert wahrscheinlich auch)
- Python 3.11 oder neuer
- Für lokale Transkription: `pip install faster-whisper`
- Für Textverbesserung, Dampf ablassen, Emojis und Protokoll: OpenAI API Key mit Zugriff auf `gpt-4o-mini` und `gpt-4o`
- Für Online-Transkription: OpenAI API Key mit Zugriff auf `whisper-1`
- Mikrofon

## Installation

```bat
git clone https://github.com/Regdar76/Blitzdiktat.git
cd Blitzdiktat\BlitzdiktatWin
pip install -r requirements.txt
```

Empfohlen: virtuelle Umgebung verwenden:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Starten

```bat
run.bat
```

Oder direkt:

```bat
python main.py
```

Beim ersten Start öffnet sich das Hauptfenster automatisch. Dort oder über „Einstellungen" den OpenAI API Key eintragen — er wird sicher im Windows Credential Manager gespeichert.

## Bedienung

**Tastenkürzel (Haltenmodus):**
Tastenkürzel gedrückt halten → sprechen → loslassen → Text wird transkribiert und in das zuletzt aktive Fenster eingefügt.

**Tray-Icon:**
- Links- oder Rechtsklick → Menü mit allen Workflows und Einstellungen.
- Farbe zeigt Status: blau = bereit, rot = Aufnahme, gelb = Verarbeitung, grün = fertig.

**Hauptfenster:**
Workflow-Schaltfläche klicken → Aufnahme startet. Nochmals klicken → Aufnahme stoppt und Verarbeitung beginnt.

## Projektstruktur

```
BlitzdiktatWin/
  main.py              Einstiegspunkt
  app_state.py         Zentraler App-State
  services/
    credentials_service.py          Windows Credential Manager
    audio_recorder.py               Mikrofonaufnahme (sounddevice)
    transcription_service.py        Dispatcher: lokal oder online
    local_transcription_service.py  Offline-Transkription (faster-whisper)
    llm_service.py                  OpenAI Chat Completions
    hotkey_service.py               Globale Tastenkürzel (pynput)
    paste_service.py                Zwischenablage + Ctrl+V Simulation
    transcript_store.py             Speichert Transkripte und Protokoll-PDFs
  features/
    workflows/         Transcription, TextImprovement, DampfAblassen, EmojiText, Protokoll
    tray/              System-Tray-Icon (pystray)
    ui/                Hauptfenster + Einstellungsfenster (customtkinter)
  requirements.txt
  run.bat
```

## Lokale Transkription

Offline-Transkription via `faster-whisper` ist vollständig implementiert und ist der Standard-Modus. Beim ersten Einsatz lädt die App das gewählte Modell automatisch herunter und speichert es in:

```
%APPDATA%\Blitzdiktat\whisper_models\
```

Verfügbare Modelle: tiny, base, small (Standard, empfohlen), medium, large-v3.

Siehe [../docs/local-models.md](../docs/local-models.md) für Details.

## Gespeicherte Transkripte

Alle Workflow-Ausgaben werden automatisch als `.txt`-Datei gespeichert:

```
%LOCALAPPDATA%\Blitzdiktat\Transkriptionen\
```

Protokoll-Ausgaben werden zusätzlich als formatiertes `.pdf` im selben Ordner gespeichert. Dateien, die älter als 14 Tage sind, werden automatisch bereinigt.

## Datenschutz

```
Lokale Transkription:   Dein PC → faster-whisper auf dem Gerät (kein Netzwerk)
Online-Transkription:   Dein PC → OpenAI Audio Transcriptions API
Text-Rewriting:         Dein PC → OpenAI Chat Completions API
```

Kein eigenes Backend. Der API Key liegt im Windows Credential Manager.
Lies [../docs/privacy.md](../docs/privacy.md) vor dem Einsatz mit sensiblen Inhalten.

## Lizenz

MIT — gleich wie das Hauptprojekt. Siehe [../LICENSE](../LICENSE).
