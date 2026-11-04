from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QScrollArea

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

ARTIFACTS = Path(__file__).resolve().parent
APP = QApplication.instance() or QApplication([])
project = new_design_project("SYNTHETIC cross-study CSV window verification")
project["study_references"] = []
for study_name in ("A", "B"):
    study_id = f"synthetic-study-{study_name}"
    study_path = ARTIFACTS / f"{study_id}.study.json"
    study_manifest = {
        "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1", "study_id": study_id,
        "project_id": project["project_id"], "baseline_engine_identity_sha256": "9" * 64,
        "scientific_validation": "NOT_CLAIMED", "parameter": {"id": "exhaust:length", "label": "Escape", "unit": "mm"},
        "points": [],
    }
    raw = json.dumps(study_manifest, sort_keys=True, separators=(",", ":")).encode()
    study_path.write_bytes(raw)
    project["study_references"].append({
        "path": str(study_path), "study_id": study_id, "source_project_id": project["project_id"],
        "schema": study_manifest["schema"], "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    })
window = DinoDesktopWindow(project)
window.resize(1440, 900)
window.show()
window.analysis_mode.click()
page = window.results
page.result_tabs.setCurrentIndex(3)
destination = ARTIFACTS / "synthetic-comparison.csv"
QFileDialog.getSaveFileName = lambda *args: (str(destination), "CSV (*.csv)")

baseline = "9" * 64


def point(study, index, rpm, value, periodicity, classification, code):
    identity = code * 64
    return {
        "index": index, "value": value, "unit": "mm", "rpm": rpm,
        "status": "COMPLETE", "classification": classification, "periodicity": periodicity,
        "cycles_completed": 2, "run_id": f"synthetic-{study}-{index}",
        "source_run_id": f"synthetic-{study}-{index}", "engine_identity_sha256": identity,
        "identity_sha256": code.swapcase() * 64, "result_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "result_artifact_sha256": hashlib.sha256((code + "artifact").encode()).hexdigest(),
        "run_directory": f"SYNTHETIC/{study}/{index}", "source_verified": False,
        "metrics": {"brake_power": None, "brake_torque": None, "BMEP": None},
        "source_manifest_point": {"index": index, "value": value, "unit": "mm",
                                  "factor_values": [{"label": "Escape", "value": value, "unit": "mm"}]},
    }


point_a = point("A", 0, 3000.0, 38.40862784470379, "INSUFFICIENT_CYCLES", "MAX_CYCLES_NONCONVERGED", "a")
point_b = point("B", 0, 3000.0, 39.40862784470379, "INSUFFICIENT_CYCLES", "MAX_CYCLES_NONCONVERGED", "b")
point_unpaired = point("B", 1, 4000.0, 40.123456789, "NOT_EVALUATED", "NOT_STARTED", "c")
comparison = {
    "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
    "baseline_engine_identity_sha256": baseline,
    "scientific_validation": "NOT_CLAIMED",
    "notice": "Fixture sintético de interfaz; no es evidencia de cálculo.",
    "studies": [
        {"study_id": ref["study_id"], "manifest_path": ref["path"],
         "manifest_sha256": ref["manifest_sha256"], "parameter": {"label": "Escape"}}
        for ref in project["study_references"]
    ],
    "pairs": [{"study_a": "synthetic-study-A", "point_a": point_a,
                "study_b": "synthetic-study-B", "point_b": point_b, "rpm": 3000.0,
                "pairing": "EXACT_RPM_AND_OPERATING_CONTEXT",
                "metrics": {key: {"a": None, "b": None, "delta": None}
                            for key in ("brake_power", "brake_torque", "BMEP")}}],
    "unpaired": [{"study_id": "synthetic-study-B", "point": point_unpaired,
                  "reason": "Fixture sintético: sin punto compatible a 4000 RPM."}],
}
receipt = {"schema": "DINO_NATIVE_CROSS_STUDY_CSV_CHECK_V1", "synthetic": True}


def exercise():
    page._study_comparison_loaded(comparison)
    APP.processEvents()
    scroll = page.result_tabs.widget(3)
    if isinstance(scroll, QScrollArea):
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        APP.processEvents()
    page.study_comparison_table.selectRow(0)
    exported = page.export_study_comparison_csv()
    APP.processEvents()
    with destination.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    screenshot = ARTIFACTS / "native-cross-study-csv.png"
    window.grab().save(str(screenshot))
    receipt.update({
        "native_window_visible": window.isVisible(),
        "outer_size": [window.width(), window.height()],
        "comparison_rows_visible": page.study_comparison_table.rowCount(),
        "csv_export_action_succeeded": exported,
        "csv_rows": len(rows),
        "row_types": [row["row_type"] for row in rows],
        "nonperiodic_metrics_blank": rows[0]["brake_power_delta_kw"] == "",
        "unpaired_reason_preserved": rows[1]["pairing_reason"],
        "csv_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "screenshot": screenshot.name,
        "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
    })
    (ARTIFACTS / "native-window-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    window.close()
    APP.quit()


QTimer.singleShot(1200, exercise)
APP.exec()
