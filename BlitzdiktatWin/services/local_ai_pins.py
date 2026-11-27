# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Festgelegte Version von LM Studio für die automatische Einrichtung.

Dieselben Werte stehen in installer_lokale_ki.iss (Setup); ein Test prüft, dass
beide übereinstimmen. Neue Version eintragen:  winget show --id ElementLabs.LMStudio -e
(liefert Adresse und Prüfsumme), Größe in Bytes aus dem Download.
"""

LM_STUDIO_VERSION = "0.4.29-2"
LM_STUDIO_URL = f"https://installers.lmstudio.ai/win32/x64/{LM_STUDIO_VERSION}/LM-Studio-{LM_STUDIO_VERSION}-x64.exe"
LM_STUDIO_SHA256 = "969dc4f02f44b215fc68e3ba71f6832359b688e71fd7b0c02d863fbb536c9647"
LM_STUDIO_BYTES = 654595456
