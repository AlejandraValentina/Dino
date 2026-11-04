from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

_PYWIN32_DLL_DIRECTORY = None
if os.environ.get("DINO_UIA_DEPS"):
    _PYWIN32_DLL_DIRECTORY = os.add_dll_directory(
        str(Path(os.environ["DINO_UIA_DEPS"]) / "pywin32_system32"))
import win32con
import win32gui
from pywinauto import Desktop

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "results" / "desktop-ui-automation-com-repro" / "child_desktop.py"
TITLE = "Dino UIA COM Lifecycle Repro"
PROGRESS = ROOT / "results" / "desktop-ui-automation-com-repro" / "uia-progress.jsonl"


def main():
    current_stage = "START"
    observed_stages = []
    def mark(value):
        nonlocal current_stage
        current_stage=value
        observed_stages.append(value)
        with PROGRESS.open("a",encoding="utf-8") as stream:
            stream.write(json.dumps({"stage":value,"monotonic":time.monotonic()})+"\n")
            stream.flush()
        print(value, flush=True)
    env = os.environ.copy()
    env.pop("QT_QPA_PLATFORM", None)
    with tempfile.TemporaryDirectory(prefix="dino-uia-ready-") as temp:
        ready = Path(temp) / "ready.txt"
        child = subprocess.Popen([sys.executable, str(CHILD), str(ready)], cwd=ROOT, env=env)
        wrapper = None
        error = None
        checks = {}
        try:
            mark("START_CHILD")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not ready.exists() and child.poll() is None:
                time.sleep(0.1)
            if not ready.exists():
                raise RuntimeError("Desktop child did not report visible-window readiness")

            mark("CHILD_WINDOW_VISIBLE")
            desktop = Desktop(backend="uia")
            wrapper = desktop.window(title=TITLE)
            mark("BEFORE_UIA_WAIT_VISIBLE")
            wrapper.wait("exists visible enabled", timeout=30)
            mark("AFTER_UIA_WAIT_VISIBLE")
            hwnd = wrapper.handle
            mark("GOT_UIA_HANDLE")
            matches=[]
            def collect_window(candidate, _):
                if win32gui.IsWindowVisible(candidate) and win32gui.GetWindowText(candidate)==TITLE:
                    matches.append(candidate)
                return True
            win32gui.EnumWindows(collect_window, None)
            checks.update({
                "window_title": wrapper.window_text(),
                "window_handle": hwnd,
                "window_visible_before_close": bool(wrapper.is_visible()),
                "uia_descendant_count_before_close": int(wrapper.descendants().__len__()),
                "matching_top_windows_before_close": len(matches),
            })
            mark("GOT_UIA_DESCENDANTS")

            # Reproduce the historical sequence: close through Win32, then ask
            # the retained UIA wrapper to query visibility after provider teardown.
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            mark("POSTED_WM_CLOSE")
            try:
                mark("BEFORE_UIA_WAIT_NOT_VISIBLE")
                wrapper.wait_not("visible", timeout=5)
                mark("AFTER_UIA_WAIT_NOT_VISIBLE")
                checks["uia_post_close_wait"] = "RETURNED_NORMALLY"
            except BaseException as exc:
                error = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "hresult": getattr(exc, "hresult", None),
                    "traceback": traceback.format_exc(),
                }
                checks["uia_post_close_wait"] = "RAISED"
            checks["win32_window_visible_after_close"] = bool(win32gui.IsWindowVisible(hwnd))
            try:
                child_exit = child.wait(timeout=15)
                checks["child_exit_code"] = child_exit
                checks["child_process_alive_after_close"] = False
            except subprocess.TimeoutExpired:
                checks["child_process_alive_after_close"] = True
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
        except BaseException as exc:
            error={"stage":current_stage,"type":type(exc).__name__,"message":str(exc),
                "hresult":getattr(exc,"hresult",None),"traceback":traceback.format_exc()}
            checks["failure_stage"]=current_stage
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
            checks.setdefault("child_process_alive_after_cleanup", child.poll() is None)
        receipt = {
            "schema": "DINO_UIA_COM_LIFECYCLE_REPRO_V1",
            "fixture_origin": "synthetic Desktop window; no solver execution",
            "versions": {"python": sys.version.split()[0]},
            "observed_stages":observed_stages,
            "checks": checks,
            "captured_exception": error,
            "corrected_observation": {
                "uses_win32_is_window_visible_after_close": checks.get("win32_window_visible_after_close") is False,
                "no_child_process_left": checks.get("child_process_alive_after_close") is False,
            },
        }
        output = ROOT / "results" / "desktop-ui-automation-com-repro" / "reproduction-receipt.json"
        output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))
        if not (checks.get("window_visible_before_close") and checks.get("matching_top_windows_before_close") == 1
                and checks.get("win32_window_visible_after_close") is False
                and checks.get("child_process_alive_after_close") is False):
            raise SystemExit("Native/UIA lifecycle reproduction failed acceptance")


if __name__ == "__main__":
    main()
