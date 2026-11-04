"""Packaged Dino Desktop smoke test for the synthetic historical report export."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from pywinauto import Application, Desktop


def wait_for(predicate, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.2)
    raise TimeoutError("Windows UIA condition timed out")


def dialog_path(title_fragment, path):
    dialog = wait_for(lambda: next((w for w in Desktop(backend="uia").windows()
        if title_fragment.casefold() in w.window_text().casefold()), None))
    edit = wait_for(lambda: next((item for item in dialog.descendants()
        if item.element_info.control_type == "Edit"), None))
    edit.set_edit_text(str(path))
    edit.set_focus()
    dialog.type_keys("{ENTER}")
    time.sleep(.4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    output = args.work / "informe-tecnico-sintetico.html"
    if output.exists():
        raise FileExistsError(output)
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "QT_PLUGIN_PATH",
                "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORM"):
        env.pop(key, None)
    env["LOCALAPPDATA"] = str(args.work / "LocalAppData")
    env["QT_SCALE_FACTOR"] = "1"
    app = Application(backend="uia").start(str(args.exe.resolve()), work_dir=str(args.work), env=env)
    main_window = app.window(title_re=r"Dino 2T.*")
    main_window.wait("visible enabled", timeout=40)
    main_window.child_window(title="RESULTADOS", control_type="Button").click_input()
    main_window.child_window(title="Importar resultados…", control_type="Button").click_input()
    dialog_path("Importar resultados", args.csv.resolve())
    wait_for(lambda: "30 puntos" in "\n".join(x.window_text() for x in main_window.descendants()), 40)
    main_window.capture_as_image().save(str(args.work / "01-resultados-sinteticos.png"))
    main_window.child_window(title="Exportar informe técnico HTML…", control_type="Button").click_input()
    dialog_path("Exportar informe técnico", output)
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
    main_window.capture_as_image().save(str(args.work / "02-informe-exportado.png"))
    main_window.close()
    main_window.wait_not("visible", timeout=10)
    result = {"exe": str(args.exe.resolve()), "input_csv": str(args.csv.resolve()),
              "input_kind": "existing synthetic historical 30-point dataset",
              "output_html": str(output), "checks": checks,
              "main_process_windows_after_close": len(Desktop(backend="win32").windows(process=app.process))}
    (args.work / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
