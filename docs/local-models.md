# Lokale Modelle

Die Transkription läuft lokal — ohne API-Key, Audio verlässt das Gerät nicht:

- **Windows:** `faster-whisper` (CTranslate2-Backend)
- **macOS:** WhisperKit
- **Android:** On-Device-Spracherkennung des Systems (kein Whisper; whisper.cpp ist auf der [Roadmap](../ROADMAP.md))

## Verfügbare Whisper-Modelle (Windows)

| Modell | Größe | Hinweis |
|---|---|---|
| tiny | ~75 MB | Sehr schnell, weniger genau |
| base | ~150 MB | Schnell |
| small | ~500 MB | Guter Kompromiss — **empfohlener Standard** |
| medium | ~1,5 GB | Genauer |
| large-v3 | ~3 GB | Beste Qualität |

Alle Modelle sind mehrsprachig (Deutsch, Englisch und viele weitere Sprachen).

## Modell-Cache

```
%APPDATA%\Blitzdiktat\whisper_models\
```

Der Ordner wird automatisch angelegt. Modelle werden beim ersten Einsatz von Hugging Face geladen — sie liegen der App nicht bei.

## Modell wählen

**Einstellungen → Transkription** → Modell im Dropdown wählen. Das gewählte Modell lädt beim ersten Einsatz; danach kommt es direkt aus dem Cache. Für die meisten Fälle ist **small** die richtige Wahl; **tiny**/**base** bei knappem Speicher oder langsamer Verbindung.

## faster-whisper installieren

```bat
pip install faster-whisper
```

Danach die App neu starten. Fehlt das Paket, zeigt die App eine Warnung und bietet ersatzweise die Online-Transkription mit OpenAI-Key an.

## Hinweise

- Der erste Lauf nach einem Modellwechsel ist langsamer (Download + erstes Laden).
- Modelle laufen standardmäßig auf der CPU mit `int8`-Quantisierung — funktioniert ohne GPU.
- Lokale Transkription vermeidet das Senden von Audio an externe Dienste; der Schreib-Schritt der LLM-Workflows nutzt weiterhin OpenAI.
- Prüfsummen der Modelle werden nach dem Download derzeit nicht verifiziert ([Roadmap](../ROADMAP.md)).
