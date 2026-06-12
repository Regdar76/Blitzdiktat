# Roadmap

Arbeitsliste für die Weiterentwicklung — keine Zusagen, nur Richtung.

## Aktueller Stand

| | Windows 2.1.3 | Android 0.3.0 | macOS (Blitztext) |
|---|---|---|---|
| Diktat lokal | ✅ faster-whisper | ✅ Geräte-Erkennung | ✅ WhisperKit |
| LLM-Workflows (+, $%&!, :)) | ✅ | ✅ | ✅ |
| Protokoll (+ PDF) | ✅ | ✅ | — |
| Verlauf (14 Tage) | ✅ | ✅ | teilweise |
| Vokabular (manuell + gelernt) | ✅ | ✅ | — |
| Eigene Prompts/Namen je Workflow | ✅ | ✅ | — |
| Tests + CI | ✅ pytest | ✅ JUnit | Build-Job |

## Windows

- Erster Start klarer machen, v. a. Feedback beim Modell-Download
- Credential-Setup, -Validierung und -Wiederherstellung verbessern
- Provider-Grenzen schärfen, damit OpenAI und lokale Transkription sauber austauschbar sind
- Lokales Text-Rewriting, damit auch die Schreib-Workflows offline laufen können
- Protokoll: Sprechererkennung, automatische Spracherkennung, eigene Vorlagen
- Prüfsummen-Verifikation für heruntergeladene Whisper-Modelle
- Installer-Pflege (Inno Setup liegt bei, Releases nach Bedarf)

## Android

- **whisper.cpp per JNI** für echte Whisper-Qualität offline — löst auch:
  - Vokabular beim reinen Diktat (Begriffsliste als Whisper-Prompt)
  - Audio-Datei-Import für das Protokoll (bisher nur Textdateien)
  - lückenlose Protokoll-Aufnahme (SpeechRecognizer verliert beim Segment-Neustart kurze Stücke)
- Strings nach `strings.xml`, sauberes Dark-Theme statt hartkodierter Farben
- `security-crypto` (abgekündigt) durch eigene Keystore-Lösung ersetzen
- Release-Builds mit Minify/ProGuard, sobald auf Geräten getestet

## macOS

- Protokoll-Workflow nachziehen (inkl. PDF-Export)
- Verlauf und Vokabular auf den Stand von Windows/Android bringen
- Eigene Prompts/Namen je Workflow

## Bewusst nicht geplant

- Gehostetes Backend, Accounts, Sync oder Teams
- Eingebetteter API-Key in verteilten Apps
- Veröffentlichung des Repositories (bleibt privat)
