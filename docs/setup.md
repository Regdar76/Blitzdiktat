# Setup (Windows)

Einrichtung der Windows-App auf einem neuen Rechner. Für Android und macOS siehe das jeweilige README ([Android](../BlitzdiktatAndroid/README.md) · [macOS](../BlitztextMac/README.md)).

## 1. Voraussetzungen

- Windows 11 (Windows 10 funktioniert wahrscheinlich auch)
- Python 3.11 oder neuer
- Ein Mikrofon
- Für lokale Transkription: `faster-whisper` (Schritt 3)
- Für Online-Transkription und alle Schreib-Workflows: ein OpenAI API Key

## 2. Klonen und installieren

```bat
git clone https://github.com/Regdar76/Blitzdiktat.git
cd Blitzdiktat\BlitzdiktatWin
```

Empfohlen: virtuelle Umgebung:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Lokale Transkription (empfohlen)

Die lokale Transkription läuft komplett offline über `faster-whisper` und ist der Standard-Modus.

```bat
pip install faster-whisper
```

Beim ersten Einsatz lädt die App das gewählte Whisper-Modell automatisch von Hugging Face und speichert es in `%APPDATA%\Blitzdiktat\whisper_models\`. Standard ist **Small (~500 MB)** — der Download passiert einmalig im Hintergrund.

Alle Modelle und Größen: [local-models.md](local-models.md).

## 4. OpenAI für Online- und Schreib-Workflows

In den App-Einstellungen den eigenen OpenAI API Key eintragen, falls gewünscht:

- Online-Transkription (`whisper-1`)
- Textverbesserung (`gpt-4o-mini`)
- Dampf ablassen (`gpt-4o`)
- Emojis (`gpt-4o-mini`)
- Protokoll (`gpt-4o`)

API-Zugang, Abrechnung und Datenhandling laufen über das eigene OpenAI-Konto. Den Key niemals ins Repository, in Issues, Logs oder Screenshots packen.

Wer nur lokal diktieren will, kann diesen Schritt komplett überspringen.

## 5. Starten

```bat
run.bat
```

Oder direkt: `python main.py`. Beim ersten Start öffnet sich das Hauptfenster automatisch; der Key wandert in den Windows Credential Manager.

## 6. Mikrofon-Berechtigung

Falls die App nicht auf das Mikrofon zugreifen kann:

**Einstellungen → Datenschutz und Sicherheit → Mikrofon → Desktop-Apps den Zugriff erlauben**

## Fehlerbehebung

- **`faster-whisper` nicht gefunden:** `pip install faster-whisper`, dann App neu starten.
- **Modell-Download langsam:** Small (~500 MB) lädt einmalig; für schnelleren Start Tiny (~75 MB) wählen.
- **Online-Transkription schlägt sofort fehl:** Key in den Einstellungen vorhanden und gültig?
- **Einfügen funktioniert nicht:** Der Mechanismus simuliert `Ctrl+V` — prüfen, ob etwas den Zwischenablage-Zugriff blockiert.
- **Kein/leises Audio:** Mikrofon-Berechtigung und Geräteauswahl in den App-Einstellungen prüfen.
- **OpenAI-Fehler:** Modellzugriff und Abrechnungsstatus im OpenAI-Konto prüfen.
- **`hotkey_protokoll` wird nicht gespeichert:** Bei einer `settings.json` aus einer älteren Version `"hotkey_protokoll": "ctrl+shift+p"` manuell ergänzen oder die Datei löschen (Reset auf Standardwerte).
