# Copyright (c) 2026 Thorben Meier. MIT License.
r"""
Clipboard + keyboard simulation for auto-paste on Windows.

Strategy (in order):
  1. Always write text to clipboard  →  user can always Ctrl+V manually
  2. Find the focused child control inside the target window
  3a. If it is a standard Win32 edit control  →  WM_PASTE directly (no focus steal)
  3b. Otherwise  →  AttachThreadInput + SetForegroundWindow + SendInput(Ctrl+V)

Debug mode: set env var BLITZDIKTAT_DEBUG=1 before launching.
Log is written to %APPDATA%\Blitzdiktat\debug.log
"""

import os
import time
import threading
import ctypes
import ctypes.wintypes

_user32   = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_OWN_PID  = os.getpid()

# ── Fix return types (default c_int truncates 64-bit HWNDs / pointers) ────
# GetForegroundWindow / GetFocus return HWND (pointer-sized handle).
# c_size_t is unsigned and pointer-width — safe on both 32- and 64-bit.
_user32.GetForegroundWindow.restype          = ctypes.c_size_t
_user32.GetFocus.restype                     = ctypes.c_size_t
_user32.FindWindowW.restype                  = ctypes.c_size_t
_user32.GetWindowThreadProcessId.restype     = ctypes.wintypes.DWORD
_kernel32.GetCurrentThreadId.restype         = ctypes.wintypes.DWORD
# GlobalAlloc / GlobalLock return HGLOBAL / LPVOID (pointer-sized)
_kernel32.GlobalAlloc.restype    = ctypes.c_void_p
_kernel32.GlobalAlloc.argtypes   = [ctypes.wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalLock.restype     = ctypes.c_void_p
_kernel32.GlobalLock.argtypes    = [ctypes.c_void_p]   # HGLOBAL is pointer-sized
_kernel32.GlobalUnlock.argtypes  = [ctypes.c_void_p]
# SetClipboardData second arg is HANDLE (pointer-sized) — must not default to c_int
_user32.SetClipboardData.argtypes = [ctypes.wintypes.UINT, ctypes.c_void_p]
_user32.SetClipboardData.restype  = ctypes.c_void_p
# SendMessageW: HWND + WPARAM/LPARAM are pointer-sized — declare them so 64-bit
# window handles are not truncated to c_int. (Note: ctypes only exposes the
# *W/*A variants, never a bare "SendMessage".)
_user32.SendMessageW.argtypes = [ctypes.c_size_t, ctypes.wintypes.UINT,
                                 ctypes.c_size_t, ctypes.c_size_t]
_user32.SendMessageW.restype  = ctypes.c_ssize_t

# ── Win32 constants ────────────────────────────────────────────────────────
_WM_PASTE         = 0x0302
_WM_GETTEXTLENGTH = 0x000E
_EM_REPLACESEL    = 0x00C2
_SW_RESTORE       = 9
_INPUT_KEYBOARD     = 1
_KEYEVENTF_KEYUP    = 0x0002
_KEYEVENTF_SCANCODE = 0x0008
_MAPVK_VK_TO_VSC    = 0
_VK_CONTROL         = 0x11
_VK_V               = 0x56
_CF_UNICODETEXT     = 13

# Sentinel written into dwExtraInfo of our synthetic key events, so we can
# tell them apart from real keystrokes if we ever need to.
_INJECT_TAG = 0x424C_495A   # 'BLIZ'

# Scan codes resolved once at import; used for the synthetic Ctrl+V fallback.
_user32.MapVirtualKeyW.restype  = ctypes.wintypes.UINT
_user32.MapVirtualKeyW.argtypes = [ctypes.wintypes.UINT, ctypes.wintypes.UINT]
_SCAN_CONTROL = _user32.MapVirtualKeyW(_VK_CONTROL, _MAPVK_VK_TO_VSC)
_SCAN_V       = _user32.MapVirtualKeyW(_VK_V,       _MAPVK_VK_TO_VSC)

# Edit/RichEdit-family controls accept EM_REPLACESEL, which inserts text
# straight into the control's buffer at the caret — no clipboard, no focus, no
# paste accelerator. "richeditd2dpt" is the edit surface of the Windows 11
# "Editor"/Notepad. (The modern Notepad receives WM_PASTE but treats it as a
# no-op when sent from another process; EM_REPLACESEL writes the text directly.)
_RICHEDIT_CLASSES = frozenset({
    "edit", "richedit", "richedit20w", "richedit20a",
    "richedit50w", "richeditd2dpt",
})
# Scintilla (Notepad++) does not implement EM_REPLACESEL, but WM_PASTE works.
_SCINTILLA_CLASSES = frozenset({"scintilla"})
# Union: any control we can drive without simulating keystrokes.
_PASTE_MSG_CLASSES = _RICHEDIT_CLASSES | _SCINTILLA_CLASSES

# ── Debug logging ──────────────────────────────────────────────────────────
# Opt-in: set BLITZDIKTAT_DEBUG=1 to log paste attempts to
# %APPDATA%\Blitzdiktat\debug.log. Diktat-Inhalte werden nie geloggt.
_DEBUG = os.environ.get("BLITZDIKTAT_DEBUG", "").strip() == "1"
_log_lock = threading.Lock()


def _log(msg: str) -> None:
    if not _DEBUG:
        return
    import datetime
    app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    log_path = os.path.join(app_data, "Blitzdiktat", "debug.log")
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}\n"
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with _log_lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        pass


# ── Foreground-window tracker ──────────────────────────────────────────────
_own_hwnds:          set[int] = set()
_last_external_hwnd: int      = 0
_tracker_started:    bool     = False
_tracker_lock = threading.Lock()


def _is_own_window(hwnd: int) -> bool:
    """True if hwnd belongs to Blitzdiktat's own process (covers tray/pystray windows too)."""
    if hwnd in _own_hwnds:
        return True
    pid = ctypes.wintypes.DWORD(0)
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == _OWN_PID


def register_own_window(hwnd: int) -> None:
    normalized = int(hwnd) & 0xFFFF_FFFF_FFFF_FFFF  # ensure unsigned
    _own_hwnds.add(normalized)
    _log(f"register_own_window: {hex(hwnd)} (normalized={hex(normalized)}) "
         f"→ own={[hex(h) for h in _own_hwnds]}")


def start_foreground_tracker() -> None:
    global _tracker_started
    with _tracker_lock:
        if _tracker_started:
            return
        _tracker_started = True

    def _loop() -> None:
        global _last_external_hwnd
        while True:
            raw = _user32.GetForegroundWindow()
            h = int(raw or 0) & 0xFFFF_FFFF_FFFF_FFFF
            if h and not _is_own_window(h):
                if _last_external_hwnd != h:
                    _log(f"tracker: new external fg={hex(h)}")
                _last_external_hwnd = h
            time.sleep(0.1)

    threading.Thread(target=_loop, daemon=True, name="FgTracker").start()
    _log("start_foreground_tracker: started")


def get_foreground_hwnd() -> int:
    raw = _user32.GetForegroundWindow()
    h = int(raw or 0) & 0xFFFF_FFFF_FFFF_FFFF
    _log(
        f"get_foreground_hwnd: current={hex(h)}, "
        f"own={[hex(x) for x in _own_hwnds]}, "
        f"last_ext={hex(_last_external_hwnd)}"
    )
    if h and not _is_own_window(h):
        return h
    result = _last_external_hwnd or h
    _log(f"get_foreground_hwnd: own-window active → returning last_ext={hex(result)}")
    return result


# ── Public API ─────────────────────────────────────────────────────────────

def paste_to_window(hwnd: int, text: str) -> None:
    _log(f"paste_to_window: hwnd={hex(hwnd)}, text_len={len(text)}")

    # 1. Clipboard first — always, so manual Ctrl+V works regardless
    clip_ok = _write_clipboard(text)
    _log(f"paste_to_window: clipboard_write={'ok' if clip_ok else 'FAILED'}")

    if not hwnd:
        _log("paste_to_window: hwnd=0, skipping inject (text is in clipboard)")
        return

    is_valid = bool(_user32.IsWindow(hwnd))
    _log(f"paste_to_window: IsWindow({hex(hwnd)})={is_valid}")
    if not is_valid:
        _log("paste_to_window: hwnd is stale/invalid, skipping inject")
        return

    # 2. Try to find the focused child control inside the target window
    focused = _get_focused_child(hwnd)
    cls = _get_class_name(focused) if focused else ""
    _log(f"paste_to_window: focused_child={hex(focused)}, class={repr(cls)}")

    lc = cls.lower() if focused else ""

    # 3a. Edit/RichEdit-family (incl. Windows 11 Notepad) → EM_REPLACESEL inserts
    #     the text directly into the control. Verified via a text-length delta;
    #     if nothing was inserted we fall through to the keystroke path.
    if focused and lc in _RICHEDIT_CLASSES:
        if _insert_via_replacesel(focused, text):
            _log("paste_to_window: EM_REPLACESEL OK")
            return
        _log("paste_to_window: EM_REPLACESEL had no effect → falling back to Ctrl+V")
        _attach_focus_paste(hwnd)
        return

    # 3b. Scintilla (Notepad++) → WM_PASTE (it does not implement EM_REPLACESEL).
    if focused and lc in _SCINTILLA_CLASSES:
        result = _user32.SendMessageW(focused, _WM_PASTE, 0, 0)
        _log(f"paste_to_window: WM_PASTE (scintilla) → result={result}")
        return

    # 3c. Everything else (Word, Outlook, browsers, Electron …) → synthetic Ctrl+V.
    _log("paste_to_window: falling back to _attach_focus_paste")
    _attach_focus_paste(hwnd)


def copy_to_clipboard(text: str) -> None:
    _write_clipboard(text)


def _insert_via_replacesel(hctrl: int, text: str) -> bool:
    """
    Insert *text* into an Edit/RichEdit control at the caret using
    EM_REPLACESEL.  Returns True if the control's text length actually grew,
    so the caller can fall back to a keystroke paste when it didn't.

    EM_REPLACESEL is one of the messages USER32 marshals across process (and
    bitness) boundaries, so the LPARAM string pointer is delivered safely.
    wParam=1 keeps the operation on the control's undo stack.
    """
    before = int(_user32.SendMessageW(hctrl, _WM_GETTEXTLENGTH, 0, 0))
    buf = ctypes.create_unicode_buffer(text)
    _user32.SendMessageW(hctrl, _EM_REPLACESEL, 1,
                         ctypes.cast(buf, ctypes.c_void_p).value)
    after = int(_user32.SendMessageW(hctrl, _WM_GETTEXTLENGTH, 0, 0))
    _log(f"_insert_via_replacesel: text_len={len(text)}, "
         f"control_len {before} → {after}")
    return after > before


# ── Internals ──────────────────────────────────────────────────────────────

def _write_clipboard(text: str) -> bool:
    for attempt in range(5):
        if _user32.OpenClipboard(0):
            break
        _log(f"_write_clipboard: OpenClipboard attempt {attempt+1} failed, retrying")
        time.sleep(0.05)
    else:
        _log("_write_clipboard: could not open clipboard after 5 attempts")
        return False
    try:
        _user32.EmptyClipboard()
        enc  = (text + "\x00").encode("utf-16-le")
        hmem = _kernel32.GlobalAlloc(0x0042, len(enc))   # GMEM_MOVEABLE|GMEM_ZEROINIT
        if not hmem:
            _log("_write_clipboard: GlobalAlloc returned NULL")
            return False
        ptr = _kernel32.GlobalLock(hmem)
        if not ptr:
            _log("_write_clipboard: GlobalLock returned NULL")
            return False
        ctypes.memmove(ptr, enc, len(enc))
        _kernel32.GlobalUnlock(hmem)
        _user32.SetClipboardData(_CF_UNICODETEXT, hmem)
        _log(f"_write_clipboard: {len(text)} chars written OK")
        return True
    except Exception as exc:
        _log(f"_write_clipboard: exception: {exc}")
        return False
    finally:
        _user32.CloseClipboard()


def _get_focused_child(hwnd: int) -> int:
    """Return the focused child control inside hwnd, using AttachThreadInput."""
    cur_tid    = int(_kernel32.GetCurrentThreadId())
    target_tid = int(_user32.GetWindowThreadProcessId(hwnd, None))
    if not target_tid or target_tid == cur_tid:
        return int(_user32.GetFocus() or 0)
    ok = _user32.AttachThreadInput(cur_tid, target_tid, True)
    try:
        return int(_user32.GetFocus() or 0)
    finally:
        if ok:
            _user32.AttachThreadInput(cur_tid, target_tid, False)


def _get_class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(64)
    _user32.GetClassNameW(hwnd, buf, 64)
    return buf.value


def _is_edit_class(hwnd: int) -> bool:
    return _get_class_name(hwnd).lower() in _PASTE_MSG_CLASSES


def _attach_focus_paste(hwnd: int) -> None:
    """
    Bring hwnd to the foreground (bypassing Windows focus-lock) and inject
    Ctrl+V via SendInput.  The thread remains attached to the target's input
    queue throughout so that both SetForegroundWindow and SendInput target
    the same thread.
    """
    cur_tid    = int(_kernel32.GetCurrentThreadId())
    fg_hwnd    = int(_user32.GetForegroundWindow() or 0)
    fg_tid     = int(_user32.GetWindowThreadProcessId(fg_hwnd, None)) if fg_hwnd else 0
    target_tid = int(_user32.GetWindowThreadProcessId(hwnd, None))

    _log(
        f"_attach_focus_paste: hwnd={hex(hwnd)}, fg_hwnd={hex(fg_hwnd)}, "
        f"fg_tid={fg_tid}, target_tid={target_tid}, cur_tid={cur_tid}"
    )

    # Attach to current foreground thread AND target thread
    att_fg  = bool(fg_tid  and fg_tid  != cur_tid and
                   _user32.AttachThreadInput(cur_tid, fg_tid,     True))
    att_tgt = bool(target_tid and target_tid != cur_tid and
                   _user32.AttachThreadInput(cur_tid, target_tid, True))

    _log(f"_attach_focus_paste: att_fg={att_fg}, att_tgt={att_tgt}")

    try:
        _user32.ShowWindow(hwnd, _SW_RESTORE)
        _user32.BringWindowToTop(hwnd)
        set_fg_ok = bool(_user32.SetForegroundWindow(hwnd))
        _log(f"_attach_focus_paste: SetForegroundWindow={set_fg_ok}")

        # Wait up to 600 ms for the window to actually gain focus
        deadline = time.monotonic() + 0.6
        while time.monotonic() < deadline:
            if int(_user32.GetForegroundWindow() or 0) == hwnd:
                break
            time.sleep(0.02)

        actual_fg = int(_user32.GetForegroundWindow() or 0)
        focus_ok  = (actual_fg == hwnd)
        _log(f"_attach_focus_paste: actual_fg={hex(actual_fg)}, focus_ok={focus_ok}")

        if not focus_ok:
            _log("_attach_focus_paste: focus transfer failed — skipping SendInput "
                 "(text is already in clipboard, user can Ctrl+V manually)")
            return

        time.sleep(0.05)   # short settle so the app is ready for input
        n = _send_input_ctrl_v()
        err = ctypes.GetLastError()
        _log(f"_attach_focus_paste: SendInput returned {n} (expected 4), "
             f"GetLastError={err}, sizeof(_INPUT)={ctypes.sizeof(_INPUT)}")
    finally:
        if att_fg:
            _user32.AttachThreadInput(cur_tid, fg_tid,     False)
        if att_tgt:
            _user32.AttachThreadInput(cur_tid, target_tid, False)


# ── SendInput structs ──────────────────────────────────────────────────────
# The union inside INPUT must include MOUSEINPUT so the union size (and thus
# sizeof(INPUT)) matches what Windows expects:
#   32-bit: sizeof(INPUT) = 28   (union = MOUSEINPUT = 24)
#   64-bit: sizeof(INPUT) = 40   (union = MOUSEINPUT = 32)
# Without MOUSEINPUT in the union, ctypes uses only KEYBDINPUT (16/24 bytes)
# → sizeof(INPUT) = 28/32 → SendInput rejects the call with ERROR_INVALID_PARAMETER.

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.wintypes.WORD),
        ("wScan",       ctypes.wintypes.WORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),   # ULONG_PTR — pointer-width value
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.wintypes.LONG),
        ("dy",          ctypes.wintypes.LONG),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]
    _anonymous_ = ("_u",)
    _fields_    = [("type", ctypes.wintypes.DWORD), ("_u", _U)]


def _send_input_ctrl_v() -> int:
    # Scan-code level events (KEYEVENTF_SCANCODE); wVk is documentation only —
    # when KEYEVENTF_SCANCODE is set Windows uses wScan. The four events are
    # sent as *separate* SendInput calls with short pauses so the target's
    # input thread registers Ctrl as down before V arrives (single-burst
    # delivery can make some apps see V without the modifier). This fallback is
    # only reached for targets without a directly drivable edit control.
    def _key(scan: int, key_up: bool) -> int:
        flags = _KEYEVENTF_SCANCODE | (_KEYEVENTF_KEYUP if key_up else 0)
        evt = (_INPUT * 1)(_INPUT(type=_INPUT_KEYBOARD, ki=_KEYBDINPUT(
            wScan=scan, dwFlags=flags, dwExtraInfo=_INJECT_TAG)))
        return _user32.SendInput(1, evt, ctypes.sizeof(_INPUT))

    n = 0
    n += _key(_SCAN_CONTROL, False); time.sleep(0.03)
    n += _key(_SCAN_V,       False); time.sleep(0.02)
    n += _key(_SCAN_V,       True);  time.sleep(0.02)
    n += _key(_SCAN_CONTROL, True)
    return n
