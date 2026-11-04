from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if os.environ.get("DINO_UIA_DEPS"):
    _dll_dir = os.add_dll_directory(str(Path(os.environ["DINO_UIA_DEPS"]) / "pywin32_system32"))
import win32con
import win32gui

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "results" / "desktop-ui-automation-com-repro" / "child_desktop.py"
TITLE = "Dino UIA COM Lifecycle Repro"

with tempfile.TemporaryDirectory(prefix="dino-win32-ready-") as temp:
    ready = Path(temp) / "ready.txt"
    env = os.environ.copy(); env.pop("QT_QPA_PLATFORM", None)
    child = subprocess.Popen([sys.executable, str(CHILD), str(ready)], cwd=ROOT, env=env)
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not ready.exists() and child.poll() is None:
            time.sleep(0.1)
        if not ready.exists(): raise RuntimeError("Desktop did not report visible window")
        handles=[]
        def collect(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd)==TITLE: handles.append(hwnd)
            return True
        win32gui.EnumWindows(collect, None)
        if len(handles)!=1: raise RuntimeError(f"Expected one visible test window, found {len(handles)}")
        hwnd=handles[0]
        before=bool(win32gui.IsWindowVisible(hwnd))
        win32gui.PostMessage(hwnd,win32con.WM_CLOSE,0,0)
        child_exit=child.wait(timeout=15)
        visible_after=bool(win32gui.IsWindowVisible(hwnd)) if win32gui.IsWindow(hwnd) else False
        receipt={"schema":"DINO_WIN32_WINDOW_LIFECYCLE_V1","fixture_origin":"synthetic; no solver run",
            "python":sys.version.split()[0],"visible_windows_before_close":len(handles),
            "window_visible_before_close":before,"window_visible_after_close":visible_after,
            "child_exit_code":child_exit,"child_process_alive_after_close":child.poll() is None,
            "close_method":"Win32 WM_CLOSE","post_close_check":"Win32 IsWindowVisible/IsWindow"}
    finally:
        if child.poll() is None:
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
output=ROOT/"results"/"desktop-ui-automation-com-repro"/"win32-lifecycle-receipt.json"
output.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,ensure_ascii=False))
if not (receipt["visible_windows_before_close"]==1 and receipt["window_visible_before_close"]
        and not receipt["window_visible_after_close"] and not receipt["child_process_alive_after_close"]):
    raise SystemExit("Win32 window lifecycle check failed")
