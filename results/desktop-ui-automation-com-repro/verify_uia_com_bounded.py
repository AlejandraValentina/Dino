from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path

_PYWIN32_DLL_DIRECTORY = None
if os.environ.get("DINO_UIA_DEPS"):
    _PYWIN32_DLL_DIRECTORY = os.add_dll_directory(
        str(Path(os.environ["DINO_UIA_DEPS"]) / "pywin32_system32"))
import win32con
import win32gui

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "results" / "desktop-ui-automation-com-repro" / "child_desktop.py"
TITLE = "Dino UIA COM Lifecycle Repro"
OUT = ROOT / "results" / "desktop-ui-automation-com-repro"
PROGRESS = OUT / "bounded-uia-progress.jsonl"
RECEIPT = OUT / "bounded-uia-receipt.json"


def main():
    if PROGRESS.exists() or RECEIPT.exists():
        raise SystemExit("Refusing to overwrite previous reproduction evidence")
    progress_lock = threading.Lock()
    stages = []
    result_queue = queue.Queue()
    close_request = threading.Event()
    attached = threading.Event()
    completed = threading.Event()

    def mark(stage):
        with progress_lock:
            stages.append(stage)
            with PROGRESS.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"stage": stage, "monotonic": time.monotonic()}) + "\n")
                stream.flush()
        print(stage, flush=True)

    def uia_worker():
        try:
            from pywinauto import Desktop
            mark("BEFORE_UIA_WAIT_VISIBLE")
            window = Desktop(backend="uia").window(title=TITLE)
            window.wait("exists visible enabled", timeout=10)
            observation = {"title": window.window_text(), "handle": window.handle,
                "visible_before_close": bool(window.is_visible())}
            result_queue.put({"attached": True, "observation": observation})
            attached.set(); mark("UIA_WINDOW_ATTACHED")
            close_request.wait(12)
            mark("BEFORE_UIA_POST_CLOSE_WAIT")
            try:
                window.wait_not("visible", timeout=5)
                result_queue.put({"post_close_wait": "RETURNED_NORMALLY"})
                mark("UIA_POST_CLOSE_WAIT_RETURNED")
            except BaseException as exc:
                result_queue.put({"post_close_wait": "RAISED", "exception": {
                    "type": type(exc).__name__, "message": str(exc),
                    "hresult": getattr(exc, "hresult", None),
                    "traceback": traceback.format_exc()}})
                mark("UIA_POST_CLOSE_WAIT_RAISED")
        except BaseException as exc:
            result_queue.put({"attached": False, "exception": {
                "type": type(exc).__name__, "message": str(exc),
                "hresult": getattr(exc, "hresult", None),
                "traceback": traceback.format_exc()}})
            mark("UIA_INITIAL_QUERY_RAISED")
        finally:
            completed.set()

    env = os.environ.copy(); env.pop("QT_QPA_PLATFORM", None)
    with tempfile.TemporaryDirectory(prefix="dino-uia-bounded-") as temp:
        ready = Path(temp) / "ready.txt"
        child = subprocess.Popen([sys.executable, str(CHILD), str(ready)], cwd=ROOT, env=env)
        worker = threading.Thread(target=uia_worker, name="uia-com-probe", daemon=True)
        win_handles=[]
        try:
            mark("START_CHILD")
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline and not ready.exists() and child.poll() is None:
                time.sleep(0.1)
            if not ready.exists():
                raise RuntimeError("Desktop child did not report visible-window readiness")
            mark("CHILD_WINDOW_VISIBLE")
            worker.start()
            uia_attached = attached.wait(12)
            if not uia_attached and not completed.is_set():
                mark("UIA_INITIAL_QUERY_TIMEOUT")
            def collect(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == TITLE:
                    win_handles.append(hwnd)
                return True
            win32gui.EnumWindows(collect, None)
            if len(win_handles) != 1:
                raise RuntimeError(f"Expected one visible test window, found {len(win_handles)}")
            hwnd=win_handles[0]
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            mark("POSTED_WIN32_WM_CLOSE")
            close_request.set()
            try:
                child_exit=child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.terminate(); child_exit=child.wait(timeout=5)
            win_visible_after=bool(win32gui.IsWindowVisible(hwnd)) if win32gui.IsWindow(hwnd) else False
            worker.join(timeout=5)
            uia_result=None
            while not result_queue.empty():
                uia_result=result_queue.get()
            receipt={"schema":"DINO_UIA_COM_LIFECYCLE_REPRO_V1",
                "fixture_origin":"synthetic Desktop window; no solver execution",
                "python":sys.version.split()[0], "uia_wait_timeout_seconds":12,
                "observed_stages":stages,"uia_attached_before_close":uia_attached,
                "uia_result":uia_result,"uia_worker_alive_after_cleanup":worker.is_alive(),
                "win32_visible_windows_before_close":len(win_handles),
                "win32_window_visible_after_close":win_visible_after,
                "child_exit_code":child_exit,"child_process_alive_after_close":child.poll() is None,
                "close_method":"Win32 WM_CLOSE","post_close_window_check":"Win32 IsWindowVisible/IsWindow"}
        finally:
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
    RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))
    if not (receipt["win32_visible_windows_before_close"] == 1
            and not receipt["win32_window_visible_after_close"]
            and not receipt["child_process_alive_after_close"]):
        raise SystemExit("Win32 cleanup failed")


if __name__ == "__main__":
    main()
