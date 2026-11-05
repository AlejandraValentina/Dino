"""Verify the Desktop export action and render a synthetic HTML comparison report."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QFileDialog, QScrollArea

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project


def locate_chrome() -> Path:
    found = shutil.which("chrome.exe")
    if found:
        return Path(found)
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                value, _ = winreg.QueryValueEx(key, None)
                candidate = Path(value)
                if candidate.is_file():
                    return candidate
        except OSError:
            continue
    raise RuntimeError("No se encontró Chrome para renderizar el HTML generado por Desktop")


def make_point(run_id: str, code: str, status: str | None, classification: str,
               periodicity: str, rpm: float, power: float | None) -> dict:
    point = {
        "index": int(rpm), "run_id": run_id, "source_run_id": run_id, "rpm": rpm,
        "classification": classification, "periodicity": periodicity,
        "engine_identity_sha256": code * 64, "identity_sha256": code.upper() * 64,
        "result_sha256": hashlib.sha256((run_id + ":result").encode()).hexdigest(),
        "result_artifact_sha256": hashlib.sha256((run_id + ":artifact").encode()).hexdigest(),
        "run_directory": f"SYNTHETIC/{run_id}",
        "metrics": {"brake_power": power, "brake_torque": None, "BMEP": None},
    }
    if status is not None:
        point["status"] = status
    return point


def main() -> int:
    out = Path(__file__).resolve().parent
    html_path = out / "synthetic-cross-study-report.html"
    browser_capture = out / "html-report-state-view-1360x2400.png"
    receipt_path = out / "capture-receipt.json"
    if any(path.exists() for path in (html_path, browser_capture, receipt_path)):
        raise SystemExit("Refusing to replace existing versioned evidence")

    baseline = "9" * 64
    a = make_point("synthetic-A-4000", "a", "COMPLETE", "PERIOD_1", "PERIOD_1", 4000.0, 15.0)
    b = make_point("synthetic-B-4000", "b", "COMPLETE", "MAX_CYCLES_NONCONVERGED",
                   "INSUFFICIENT_CYCLES", 4000.0, None)
    cancelled = make_point("synthetic-B-5000", "c", "CANCELLED_CHECKPOINTED", "NOT_STARTED",
                           "NOT_EVALUATED", 5000.0, None)
    missing_status = make_point("synthetic-A-5500", "d", None, "MAX_CYCLES_NONCONVERGED",
                                "INSUFFICIENT_CYCLES", 5500.0, None)
    studies = [
        {"study_id": "Diseño A", "source_project_id": "synthetic-project",
         "manifest_path": "SYNTHETIC/A.study.json", "manifest_sha256": "1" * 64,
         "baseline_engine_identity_sha256": baseline,
         "parameter": {"label": "Longitud de escape", "unit": "mm"}, "points": [a, missing_status]},
        {"study_id": "Diseño B", "source_project_id": "synthetic-project",
         "manifest_path": "SYNTHETIC/B.study.json", "manifest_sha256": "2" * 64,
         "baseline_engine_identity_sha256": baseline,
         "parameter": {"label": "Longitud de escape", "unit": "mm"}, "points": [b, cancelled]},
    ]
    comparison = {
        "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256": baseline,
        "scientific_validation": "NOT_CLAIMED",
        "notice": "Fixture sintético de documentación; no es una simulación ni validación.",
        "studies": studies,
        "pairs": [{"study_a": "Diseño A", "point_a": a, "study_b": "Diseño B", "point_b": b,
                   "rpm": 4000.0, "pairing": "EXACT_RPM_AND_OPERATING_CONTEXT",
                   "metrics": {"brake_power": {"a": 15.0, "b": None, "delta": None}}}],
        "unpaired": [
            {"study_id": "Diseño B", "point": cancelled, "reason": "Fixture: sin contraparte exacta."},
            {"study_id": "Diseño A", "point": missing_status, "reason": "Fixture: estado no registrado."},
        ],
    }
    app = QApplication.instance() or QApplication(sys.argv)
    window = DinoDesktopWindow(new_design_project("synthetic-report-state"))
    window.set_workspace_mode(1)
    window.resize(1360, 900)
    window.show()
    app.processEvents()
    page = window.results
    page.result_tabs.setCurrentIndex(3)
    page._study_comparison_loaded(comparison)
    app.processEvents()
    scroll = page.result_tabs.currentWidget()
    if isinstance(scroll, QScrollArea):
        content = scroll.widget()
        table_y = page.study_comparison_group.mapTo(content, QPoint(0, 0)).y()
        scroll.verticalScrollBar().setValue(max(0, table_y - 8))
        app.processEvents()
    QFileDialog.getSaveFileName = lambda *args: (str(html_path), "Informe HTML (*.html)")
    if not page.export_study_comparison():
        raise SystemExit("Desktop no pudo exportar el informe de comparación")
    html = html_path.read_text(encoding="utf-8")
    required = (
        "Ejecución:</strong> Terminada", "Clasificación:</strong> Límite de ciclos",
        "Periodicidad:</strong> Ciclos insuficientes", "Cancelada · checkpoint disponible",
        "No informada", '"status": "COMPLETE"', '"scientific_validation": "NOT_CLAIMED"',
    )
    if not all(value in html for value in required):
        raise SystemExit("El HTML no conserva los estados separados ni la procedencia sintética")
    chrome = locate_chrome()
    with tempfile.TemporaryDirectory(prefix="dino-report-state-") as profile:
        subprocess.run([str(chrome), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-first-run", "--no-default-browser-check",
                        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=10000",
                        "--window-size=1360,2400", f"--user-data-dir={profile}",
                        f"--screenshot={browser_capture}", html_path.resolve().as_uri()],
                       check=True, timeout=45, capture_output=True, text=True)
    receipt = {
        "schema": "DINO_SYNTHETIC_CROSS_STUDY_REPORT_EXECUTION_STATE_CAPTURE_V1",
        "fixture_origin": "Synthetic display/document fixture only; no solver or scientific claim",
        "desktop_window_size": [window.width(), window.height()],
        "desktop_export_action_success": True,
        "html_report_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
        "browser_capture_sha256": hashlib.sha256(browser_capture.read_bytes()).hexdigest(),
        "complete_nonconverged_endpoint_separated": all(value in html for value in required[:3]),
        "checkpointed_unpaired_endpoint_visible": "Cancelada · checkpoint disponible" in html,
        "missing_execution_status_explicit": "No informada" in html,
        "raw_comparison_preserved": '"status": "COMPLETE"' in html,
        "scientific_validation": "NOT_CLAIMED",
        "browser": "Chrome headless rendering of HTML exported by the Desktop action",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
