from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QScrollArea

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

OUT = Path(__file__).resolve().parent / "native-v5"
OUT.mkdir(parents=True, exist_ok=True)
CAPTURE = OUT / "cancelled-synthetic-study-summary.png"
RECEIPT = OUT / "receipt.json"
if CAPTURE.exists() or RECEIPT.exists():
    raise SystemExit("Refusing to replace existing evidence")

app = QApplication.instance() or QApplication([])
window = DinoDesktopWindow(new_design_project("SYNTHETIC study lifecycle summary"))
window.resize(1360, 900)
window.show()
window.analysis_mode.click()
page = window.results
page.result_tabs.setCurrentIndex(3)
page.dataset = {"points": []}
page.design_study_manifest_path = None
page.design_study_manifest = {
    "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1", "study_id": "synthetic-cancelled-study",
    "design_method": "FACTORIAL_2X2_V1", "parameter": {"label": "Escape length"}, "rpm": 3000,
    "status": "CANCELLED", "stop_reason": "CANCELLED", "total_budget_seconds": 240.0,
    "elapsed_seconds": 75.5, "scientific_validation": "NOT_CLAIMED", "points": [
        {"index": 0, "value": 0.0, "unit": "mm", "baseline": True, "status": "COMPLETE",
         "periodicity": "PERIOD_1", "classification": "PERIOD_1", "cycles_completed": 5},
        {"index": 1, "value": 1.0, "unit": "mm", "status": "MAX_CYCLES_NONCONVERGED",
         "periodicity": "INSUFFICIENT_CYCLES", "classification": "MAX_CYCLES_NONCONVERGED",
         "cycles_completed": 5},
        {"index": 2, "value": 2.0, "unit": "mm", "status": "NOT_STARTED"},
    ]}
page._update_design_study_summary()
page.design_study_group.show()
scroll = page.result_tabs.widget(3)
app.processEvents()
scroll_max=0
scroll_value=0
study_group_y=None
if isinstance(scroll, QScrollArea):
    scroll_max=scroll.verticalScrollBar().maximum()
    study_group_y=page.design_study_group.mapTo(scroll.widget(),QPoint(0,0)).y()
    scroll.verticalScrollBar().setValue(max(0,study_group_y-24))
    app.processEvents()
    scroll_value=scroll.verticalScrollBar().value()
summary = page.design_study_lifecycle_notice.text()
if not window.grab().save(str(CAPTURE)):
    raise SystemExit("Desktop capture failed")
receipt = {
    "fixture_origin": "synthetic presentation fixture; no solver execution",
    "desktop_visible": window.isVisible(), "desktop_size": [window.width(), window.height()],
    "results_scroll_max":scroll_max,"results_scroll_value":scroll_value,
    "study_group_content_y":study_group_y,
    "summary_text": summary,
    "cancelled_and_partial_points_visible": all(value in summary for value in
        ("Estado: Cancelado", "puntos completos: 1/3", "incompletos/no iniciados: 2", "cancelación solicitada")),
    "budget_visible": "Presupuesto asignado: 240 s" in summary,
    "recorded_elapsed_visible": "tiempo consumido registrado: 75.5 s" in summary,
    "no_runtime_estimate": "No se estima el tiempo restante" in summary,
    "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
}
RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False))
if not all((receipt["desktop_visible"], receipt["cancelled_and_partial_points_visible"],
            receipt["budget_visible"], receipt["recorded_elapsed_visible"], receipt["no_runtime_estimate"])):
    raise SystemExit("Desktop study lifecycle summary check failed")
window.close()
app.quit()
