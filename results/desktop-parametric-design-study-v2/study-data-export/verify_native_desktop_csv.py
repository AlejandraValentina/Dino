from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from PySide6.QtCore import QItemSelectionModel, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QScrollArea

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project


ROOT = Path(__file__).resolve().parent
APP = QApplication.instance() or QApplication([])
project = new_design_project("SYNTHETIC parametric export UI check")
study_id = "synthetic-matrix-csv-native-ui"
manifest = {
    "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1",
    "study_id": study_id,
    "project_id": project["project_id"],
    "design_method": "GEOMETRY_V1",
    "scientific_validation": "NOT_CLAIMED",
    "rpm": 3000,
    "parameter": {"id": "exhaust:length", "label": "Escape · longitud", "unit": "mm"},
    "points": [
        {"index": 0, "value": 38.40862784470379, "unit": "mm", "rpm": 3000,
         "status": "COMPLETE", "run_id": "synthetic-periodic", "source_run_id": "synthetic-periodic",
         "classification": "PERIOD_1", "periodicity": "PERIOD_1", "cycles_completed": 4,
         "engine_identity_sha256": "a" * 64, "identity_sha256": "b" * 64,
         "result_sha256": "c" * 64, "factor_values": [{"label": "Transfer top", "value": 40.123456789, "unit": "mm"}]},
        {"index": 1, "value": 42.987654321, "unit": "mm", "rpm": 3000,
         "status": "COMPLETE", "run_id": "synthetic-insufficient", "source_run_id": "synthetic-insufficient",
         "classification": "MAX_CYCLES_NONCONVERGED", "periodicity": "INSUFFICIENT_CYCLES",
         "cycles_completed": 2, "engine_identity_sha256": "d" * 64, "identity_sha256": "e" * 64,
         "result_sha256": "f" * 64, "factor_values": []},
    ],
}
manifest_path = ROOT / "synthetic-native-study.json"
manifest_raw = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
manifest_path.write_bytes(manifest_raw)
project.setdefault("study_references", []).append({
    "path": str(manifest_path), "study_id": study_id, "source_project_id": project["project_id"],
    "schema": manifest["schema"], "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
})
window = DinoDesktopWindow(project)
window.resize(1440, 900)
window.show()
window.analysis_mode.click()
page = window.results
output_path = ROOT / "synthetic-native-selected.csv"
QFileDialog.getSaveFileName = lambda *args: (str(output_path), "CSV (*.csv)")
receipt = {"schema": "DINO_NATIVE_DESKTOP_STUDY_CSV_CHECK_V1", "synthetic": True}


def exercise() -> None:
    opened = page.open_selected_project_study()
    page.result_tabs.setCurrentIndex(3)  # existing "Comparar" view
    APP.processEvents()
    compare_scroll = page.result_tabs.widget(3)
    if isinstance(compare_scroll, QScrollArea):
        compare_scroll.verticalScrollBar().setValue(compare_scroll.verticalScrollBar().maximum())
        APP.processEvents()
    page.design_study_table.selectRow(0)
    selection = page.design_study_table.selectionModel()
    selection.select(page.design_study_table.model().index(1, 0),
                     QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    exported = page.export_design_study_csv()
    APP.processEvents()
    with output_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    receipt.update({
        "native_window_visible": window.isVisible(),
        "outer_size": [window.width(), window.height()],
        "study_opened_from_project": opened,
        "rows_in_table": page.design_study_table.rowCount(),
        "export_action_succeeded": exported,
        "export_row_count": len(rows),
        "states": [row["periodicity"] for row in rows],
        "nonperiodic_metric_blank": bool(rows and rows[-1]["brake_power_kw"] == ""),
        "manifest_hash_bound": all(row["manifest_sha256"] == hashlib.sha256(manifest_raw).hexdigest() for row in rows),
        "csv_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "screenshot": "native-window-study-csv-export.png",
    })
    screenshot_path = ROOT / receipt["screenshot"]
    window.grab().save(str(screenshot_path))
    receipt["screenshot_sha256"] = hashlib.sha256(screenshot_path.read_bytes()).hexdigest()
    (ROOT / "native-window-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    window.close()
    APP.quit()


QTimer.singleShot(1500, exercise)
APP.exec()
