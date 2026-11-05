"""Capture the selected-point traceability panel with an explicit synthetic fixture."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project


def main() -> int:
    out = Path(__file__).resolve().parent
    manifest = {
        "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1",
        "study_id": "synthetic-point-status-display",
        "project_id": "synthetic-project",
        "design_method": "ONE_FACTOR_AT_A_TIME_V1",
        "rpm": 3000.0,
        "parameter": {"id": "exhaust.length", "label": "Longitud de escape", "unit": "mm"},
        "status": "COMPLETE",
        "scientific_validation": "NOT_CLAIMED",
        "points": [{
            "index": 0, "design_index": 0, "value": 83.0, "unit": "mm",
            "baseline": True, "rpm": 3000.0, "status": "COMPLETE",
            "classification": "MAX_CYCLES_NONCONVERGED",
            "periodicity": "INSUFFICIENT_CYCLES", "cycles_completed": 1,
            "run_id": "synthetic-run-000", "source_run_id": "synthetic-run-000",
            "engine_identity_sha256": "a" * 64,
            "result_sha256": "b" * 64, "result_artifact_sha256": "c" * 64,
        }],
    }
    manifest_path = out / "synthetic-point-study.json"
    raw = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    manifest_path.write_bytes(raw)
    app = QApplication.instance() or QApplication(sys.argv)
    window = DinoDesktopWindow(new_design_project("synthetic-project"))
    window.resize(1360, 900)
    window.show()
    app.processEvents()
    window.set_workspace_mode(1)
    app.processEvents()
    page = window.results
    page.open_design_study(manifest_path)
    page.design_study_table.setCurrentCell(0, 0)
    page.result_tabs.setCurrentIndex(3)
    app.processEvents()
    scroll = page.result_tabs.currentWidget()
    content = scroll.widget()
    trace_y = page.design_study_traceability_group.mapTo(content, QPoint(0, 0)).y()
    scroll.verticalScrollBar().setValue(max(0, trace_y - 8))
    app.processEvents()
    detail = page.design_study_traceability.toPlainText()
    expected = (
        "Estado de ejecución: Terminada",
        "Clasificación: Límite de ciclos · no convergida",
        "Periodicidad observada: Ciclos insuficientes",
    )
    if not all(value in detail for value in expected):
        raise SystemExit(f"La trazabilidad no separa los tres estados: {detail!r}; notice={page.design_study_notice.text()!r}; rows={page.design_study_table.rowCount()}; study={page.design_study_manifest!r}")
    image_path = out / f"native-point-execution-traceability-{window.width()}x{window.height()}.png"
    if not window.grab().save(str(image_path)):
        raise SystemExit("No se pudo guardar la captura de la ventana Qt")
    receipt = {
        "schema": "DINO_SYNTHETIC_POINT_EXECUTION_TRACEABILITY_CAPTURE_V1",
        "fixture_origin": "Synthetic UI-only manifest; no solver execution or scientific claim",
        "window_size": [window.width(), window.height()],
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "visible_state_fields": list(expected),
        "scientific_validation": "NOT_CLAIMED",
        "capture": image_path.name,
        "capture_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
    }
    (out / "capture-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
