# Blitztext für macOS

macOS-Version von [Blitzdiktat](../README.md) — gleiche Idee, gleiche Workflows, als native Menüleisten-App.

## Was es macht

| Workflow | Beschreibung |
|---|---|
| 🎙️ **Blitzdiktat** | Sprache aufnehmen → Text einfügen (lokal, ohne API-Key) |
| ✨ **Blitzdiktat+** | Aufnehmen → transkribieren → sprachlich verbessern |
| 🔥 **Blitzdiktat $%&!** | Frust rein → ruhige, sachliche Nachricht raus |
| 😊 **Blitzdiktat :)** | Text aufnehmen → passende Emojis hinzufügen |

Der Protokoll-Workflow ist auf dem Mac noch nicht umgesetzt (siehe [ROADMAP.md](../ROADMAP.md)).

## Technik

- Swift + SwiftUI, Menüleisten-App (Popover, ~340 pt)
- Globale Hotkeys über einen eigenen `HotkeyService` (Bedienungshilfen-Berechtigung nötig)
- Lokale Transkription via **WhisperKit** — Modelle werden bei Bedarf
  heruntergeladen und auf dem Gerät ausgeführt, kein API-Key nötig
- LLM-Workflows: OpenAI Chat Completions, Modelle wie auf den anderen Plattformen
- API-Key-Speicherung: macOS **Keychain**
- Start bei Anmeldung optional (`LaunchAtLoginService`)
- Aufräum-Logik für alte Aufnahmen/Transkripte (`BlitztextCleanupService`)

## Bauen

Voraussetzungen: Xcode (16+), [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`).

```bash
./build.sh            # Release-Build
./build.sh --debug    # Debug-Build
```

Das Skript erzeugt das Xcode-Projekt aus [project.yml](project.yml) und baut `Blitztext.app`. Der CI-Job `build-macos` macht dasselbe bei jedem Push.

## Berechtigungen

- **Mikrofon** — für die Aufnahme
- **Bedienungshilfen** — für globale Hotkeys und das Einfügen ins aktive Programm

## Lizenz

MIT — wie das Hauptprojekt, siehe [../LICENSE](../LICENSE).
