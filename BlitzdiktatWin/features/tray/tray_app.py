# Copyright (c) 2026 Thorben Meier. MIT License.
"""
System tray icon — equivalent to macOS MenuBarStatusController.
Provides a right-click menu for quick workflow launch and a left-click
callback to show the main window.
"""

import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw

from app_state import AppState
from features.workflows.base_workflow import WorkflowPhase, WorkflowType


def _make_icon(color: str = "#3B82F6", phase: WorkflowPhase = WorkflowPhase.IDLE) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg = {
        WorkflowPhase.IDLE: "#1E293B",
        WorkflowPhase.RECORDING: "#EF4444",
        WorkflowPhase.PROCESSING: "#F59E0B",
        WorkflowPhase.DONE: "#22C55E",
        WorkflowPhase.ERROR: "#EF4444",
    }.get(phase, "#1E293B")

    draw.ellipse([2, 2, size - 2, size - 2], fill=bg)
    # Lightning bolt
    pts = [
        (36, 4), (20, 32), (32, 32), (28, 60), (44, 32), (32, 32), (36, 4)
    ]
    draw.polygon(pts, fill="white")
    return img


class TrayApp:
    def __init__(
        self,
        app_state: AppState,
        on_show_window: Callable,
        on_quit: Callable,
    ):
        self._app_state = app_state
        self._on_show_window = on_show_window
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        app_state.subscribe(self._on_state_changed)

    def run(self) -> None:
        self._icon = pystray.Icon(
            name="Blitzdiktat",
            icon=_make_icon(),
            title="Blitzdiktat",
            menu=self._build_menu(),
        )
        self._icon.run()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        s = self._app_state.settings

        def _action(wtype: WorkflowType):
            def _cb():
                self._app_state.capture_target_window()
                # For tray-launched workflows use toggle mode (click = start, click again = stop)
                wf = self._app_state.active_workflow
                if wf and wf.workflow_type == wtype and wf.is_recording:
                    self._app_state.stop_workflow()
                else:
                    self._app_state.start_workflow(wtype)
            return _cb

        items = [
            pystray.MenuItem("⚡ Blitzdiktat", self._open_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"🎙️  {self._app_state.workflow_display_name(WorkflowType.TRANSCRIPTION)}  [{s.hotkey_transcription}]",
                _action(WorkflowType.TRANSCRIPTION),
            ),
            pystray.MenuItem(
                f"✨  {self._app_state.workflow_display_name(WorkflowType.TEXT_IMPROVER)}  [{s.hotkey_text_improver}]",
                _action(WorkflowType.TEXT_IMPROVER),
            ),
            pystray.MenuItem(
                f"🔥  {self._app_state.workflow_display_name(WorkflowType.DAMPF_ABLASSEN)}  [{s.hotkey_dampf_ablassen}]",
                _action(WorkflowType.DAMPF_ABLASSEN),
            ),
            pystray.MenuItem(
                f"😊  {self._app_state.workflow_display_name(WorkflowType.EMOJI_TEXT)}  [{s.hotkey_emoji_text}]",
                _action(WorkflowType.EMOJI_TEXT),
            ),
            pystray.MenuItem(
                f"📋  {self._app_state.workflow_display_name(WorkflowType.PROTOKOLL)}  [{s.hotkey_protokoll}]",
                _action(WorkflowType.PROTOKOLL),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️  Einstellungen", self._open_window),
            pystray.MenuItem("Beenden", self._quit),
        ]
        return pystray.Menu(*items)

    def _open_window(self) -> None:
        threading.Thread(target=self._on_show_window, daemon=True).start()

    def _quit(self) -> None:
        self._on_quit()
        self.stop()

    def _on_state_changed(self, state: AppState) -> None:
        if not self._icon:
            return
        message = state.notification
        if message:
            state.notification = None
            try:
                self._icon.notify(message, "Blitzdiktat")
            except Exception:
                pass
        wf = state.active_workflow
        phase = wf.state.phase if wf else WorkflowPhase.IDLE
        color = wf.workflow_type.color if wf else "#3B82F6"
        self._icon.icon = _make_icon(color, phase)
        self._icon.menu = self._build_menu()
