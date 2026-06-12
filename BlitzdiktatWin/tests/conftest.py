# Copyright (c) 2026 Thorben Meier. MIT License.
"""Macht das App-Verzeichnis (BlitzdiktatWin/) importierbar, egal von wo pytest läuft."""

import os
import sys

_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
