"""Packaged Dino Desktop smoke test for the synthetic historical report export."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import win32con
import win32gui
import win32process
import win32ui
from pywinauto import Application
from pywinauto.keyboard import send_keys


def wait_for(predicate, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.2)
    raise TimeoutError("Windows UIA condition timed out")


def visible_windows():
    found = []
    def visit(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            found.append((hwnd, win32process.GetWindowThreadProcessId(hwnd)[1], win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(visit, None)
    return found


def dialog_path(title_fragment, path):
    entry = wait_for(lambda: next((item for item in visible_windows()
        if title_fragment.casefold() in item[2].casefold()), None))
    win32gui.SetForegroundWindow(entry[0])
    send_keys("^a")
    send_keys(str(path), with_spaces=True)
    send_keys("{ENTER}")
    time.sleep(.4)


def save_dialog_path(title_fragment, path):
    entry = wait_for(lambda: next((item for item in visible_windows()
        if title_fragment.casefold() in item[2].casefold()), None))
    # QFileDialog opens with the report path derived from the selected source;
    # accepting that default keeps this Windows automation independent of a
    # filename edit control implementation detail.
    win32gui.SetForegroundWindow(entry[0])
    send_keys("{ENTER}")
    wait_for(lambda: path.is_file(), 15)


def capture_window(hwnd, path):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    dc = win32gui.GetWindowDC(hwnd)
    source = win32ui.CreateDCFromHandle(dc)
    memory = source.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(source, right-left, bottom-top)
    memory.SelectObject(bitmap)
    if not ctypes.windll.user32.PrintWindow(hwnd, memory.GetSafeHdc(), 2):
        raise RuntimeError("PrintWindow failed for packaged Dino Desktop")
    bitmap.SaveBitmapFile(memory, str(path))
    memory.DeleteDC(); source.DeleteDC(); win32gui.ReleaseDC(hwnd, dc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    csv = args.work / args.csv.name
    json_companion = csv.with_suffix(".json")
    shutil.copy2(args.csv, csv)
    shutil.copy2(args.csv.with_suffix(".json"), json_companion)
    output = csv.with_suffix(".informe.html")
    if output.exists():
        raise FileExistsError(output)
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "QT_PLUGIN_PATH",
                "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORM"):
        env.pop(key, None)
    env["LOCALAPPDATA"] = str(args.work / "LocalAppData")
    env["QT_SCALE_FACTOR"] = "1"
    previous_pids = {item[1] for item in visible_windows() if item[2].startswith("Dino 2T")}
    process = subprocess.Popen([str(args.exe.resolve())], cwd=args.work, env=env)
    entry = wait_for(lambda: next((item for item in visible_windows()
        if item[2].startswith("Dino 2T") and item[1] not in previous_pids), None), 40)
    app = Application(backend="uia").connect(handle=entry[0], timeout=10)
    main_window = app.window(handle=entry[0])
    main_window.wait("visible enabled", timeout=40)
    main_window.child_window(title="RESULTADOS", control_type="CheckBox").click_input()
    main_window.child_window(title="Importar resultados…", control_type="Button").click_input()
    dialog_path("Importar resultados", csv.resolve())
    wait_for(lambda: "Histórico sintético" in "\n".join(
        x.window_text() for x in main_window.descendants()), 40)
    capture_window(entry[0], args.work / "01-resultados-sinteticos.bmp")
    main_window.child_window(title="Exportar informe técnico HTML…", control_type="Button").click_input()
    save_dialog_path("Exportar informe técnico", output)
    wait_for(lambda: output.is_file(), 15)
    document = output.read_text(encoding="utf-8")
    checks = {
        "synthetic_origin": "Datos históricos sintéticos" in document,
        "experimental_validation_not_performed": "No realizada" in document,
        "thirty_points": document.count("point_id") >= 30,
        "source_and_run_identity": "Identidad y procedencia por punto" in document,
        "exact_rpm_comparisons": "RPM exactas comunes" in document,
        "self_contained_svg": "<svg" in document,
        "raw_values_preserved": "result_sha256" in document,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    capture_window(entry[0], args.work / "02-informe-exportado.bmp")
    remaining_windows = [item for item in visible_windows() if item[1] == entry[1]]
    app_windows = [item for item in remaining_windows if item[2].startswith("Dino 2T")]
    if len(app_windows) != 1:
        raise AssertionError(f"Expected one main Dino window, found {len(app_windows)}")
    win32gui.PostMessage(entry[0], win32con.WM_CLOSE, 0, 0)
    wait_for(lambda: not win32gui.IsWindowVisible(entry[0]), 10)
    remaining_windows = [item for item in visible_windows() if item[1] == entry[1]]
    result = {"exe": str(args.exe.resolve()), "input_csv": str(csv.resolve()),
              "input_kind": "existing synthetic historical 30-point dataset",
              "output_html": str(output), "checks": checks,
              "main_process_windows_after_close": len(remaining_windows)}
    (args.work / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
