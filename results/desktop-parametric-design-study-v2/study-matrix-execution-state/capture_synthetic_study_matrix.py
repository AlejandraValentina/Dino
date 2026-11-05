"""Capture the native Qt single-study result matrix using synthetic point records."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project


def main() -> int:
    out = Path(__file__).resolve().parent
    app = QApplication.instance() or QApplication(sys.argv)
    page = ResultsPage(DesktopContext(new_design_project("synthetic-study-matrix")))
    page.dataset = {"points": []}
    page.design_study_manifest = {
        "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1",
        "study_id": "synthetic-matrix-state", "design_method": "GEOMETRY_V1",
        "rpm": 3000.0, "status": "PARTIAL", "scientific_validation": "NOT_CLAIMED",
        "parameter": {"id": "exhaust.length", "label": "Longitud de escape", "unit": "mm"},
        "points": [
            {"index": 0, "design_index": 0, "baseline": True, "value": 180.0, "unit": "mm",
             "rpm": 3000.0, "status": "COMPLETE", "classification": "PERIOD_1",
             "periodicity": "PERIOD_1", "cycles_completed": 6, "run_id": "synthetic-periodic"},
            {"index": 1, "design_index": 1, "value": 182.0, "unit": "mm", "rpm": 3000.0,
             "status": "COMPLETE", "classification": "MAX_CYCLES_NONCONVERGED",
             "periodicity": "INSUFFICIENT_CYCLES", "cycles_completed": 6,
             "run_id": "synthetic-nonconverged"},
        ],
    }
    page.design_study_manifest_path = out / "synthetic-study-matrix.json"
    page._update_design_study_summary()
    table = page.design_study_table
    executions = tuple(table.item(row, 2).text() for row in range(table.rowCount()))
    classifications = tuple(table.item(row, 3).text() for row in range(table.rowCount()))
    periods = tuple(table.item(row, 4).text() for row in range(table.rowCount()))
    if executions != ("Completo", "Completo"):
        raise SystemExit(f"Estados de ejecución inesperados: {executions!r}")
    if classifications != ("Periódica · ciclo 1", "Límite de ciclos · no convergida"):
        raise SystemExit(f"Clasificaciones inesperadas: {classifications!r}")
    if periods != ("Periódica · ciclo 1", "Ciclos insuficientes"):
        raise SystemExit(f"Periodicidades inesperadas: {periods!r}")
    if tuple(table.horizontalHeaderItem(i).text() for i in (2, 3, 4)) != (
            "Ejecución", "Clasificación", "Periodicidad"):
        raise SystemExit("Los tres encabezados de estado no son independientes")
    window = QMainWindow()
    window.setWindowTitle("Dino 2T · matriz de estudio sintética")
    window.setCentralWidget(table)
    window.resize(1360, 340)
    window.show()
    app.processEvents()
    capture = out / "synthetic-study-matrix-native-1360x340.png"
    if not window.grab().save(str(capture)):
        raise SystemExit("No se pudo capturar la matriz Qt")
    receipt = {
        "schema": "DINO_SYNTHETIC_STUDY_MATRIX_EXECUTION_STATE_CAPTURE_V1",
        "fixture_origin": "Synthetic display-only study points; no solver or scientific claim",
        "headers": [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())],
        "execution_cells": list(executions),
        "classification_cells": list(classifications),
        "periodicity_cells": list(periods),
        "scientific_validation": "NOT_CLAIMED",
        "capture": capture.name,
        "capture_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
    }
    (out / "capture-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=True))
    window.close()
    page.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
