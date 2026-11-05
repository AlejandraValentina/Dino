"""Capture accessibility of independent state columns at compact and standard widths."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QFontMetrics

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project


def main() -> int:
    out = Path(__file__).resolve().parent
    app = QApplication.instance() or QApplication(sys.argv)
    page = ResultsPage(DesktopContext(new_design_project("synthetic-matrix-responsive")))
    page.dataset = {"points": []}
    page.design_study_manifest = {
        "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1", "study_id": "synthetic-responsive-matrix",
        "design_method": "GEOMETRY_V1", "rpm": 3000.0, "status": "PARTIAL",
        "scientific_validation": "NOT_CLAIMED",
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
    page.design_study_manifest_path = out / "synthetic-responsive-study.json"
    page._update_design_study_summary()
    table = page.design_study_table
    if table.columnCount() != 10 or tuple(table.horizontalHeaderItem(i).text() for i in (2, 3, 4)) != (
            "Ejecución", "Clasificación", "Periodicidad"):
        raise SystemExit("La estructura de estados de la matriz cambió")
    expected = (
        ("Completo", "Periódica · ciclo 1", "Periódica · ciclo 1"),
        ("Completo", "Límite de ciclos · no convergida", "Ciclos insuficientes"),
    )
    actual = tuple(tuple(table.item(row, col).text() for col in (2, 3, 4))
                   for row in range(table.rowCount()))
    if actual != expected:
        raise SystemExit(f"Las columnas contienen valores incorrectos: {actual!r}")
    window = QMainWindow()
    window.setWindowTitle("Dino 2T · matriz paramétrica · sintética")
    window.setCentralWidget(table)
    window.show()
    captures = {}
    for width, height in ((980, 680), (1360, 881)):
        window.resize(width, height)
        app.processEvents(); app.processEvents()
        actual_size = [window.width(), window.height()]
        if actual_size[0] != width or actual_size[1] > height:
            raise SystemExit(f"Qt no respetó el tamaño {width}x{height}: {actual_size}")
        bar = table.horizontalScrollBar()
        positions = [0]
        clipped_states=[]
        metrics=QFontMetrics(table.font())
        for row in range(table.rowCount()):
            for col in (2, 3, 4):
                cell=table.item(row,col)
                available=table.visualItemRect(cell).width()-12
                if metrics.horizontalAdvance(cell.text()) > available:
                    clipped_states.append({"row":row,"column":col,"cell_width":available,
                                           "text_width":metrics.horizontalAdvance(cell.text())})
        if clipped_states:
            raise SystemExit(f"A {width} px los textos de estado no caben completos en sus columnas: {clipped_states}")
        if bar.maximum() > 0:
            positions.append(bar.maximum())
        for position in positions:
            bar.setValue(position)
            app.processEvents()
            suffix = "left" if position == 0 else "right"
            name = f"study-matrix-{width}x{height}-{suffix}.png"
            image = out / name
            if not window.grab().save(str(image)):
                raise SystemExit(f"No se pudo capturar {name}")
            captures[name] = {"sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                              "bytes": image.stat().st_size, "scroll_value": position,
                              "scroll_maximum": bar.maximum(),
                              "state_column_widths": [table.columnWidth(i) for i in (2,3,4)]}
    receipt = {
        "schema": "DINO_SYNTHETIC_STUDY_MATRIX_RESPONSIVE_CAPTURE_V1",
        "fixture_origin": "Synthetic display-only study records; no solver or scientific claim",
        "requested_window_sizes": [[980, 680], [1360, 900]],
        "captured_window_sizes": [[980, 680], [1360, 881]],
        "1360_height_limit": "The visible Windows work area capped the Qt client height at 881 px; the table widget stayed at its normal size.",
        "state_cells": [[*row] for row in actual],
        "horizontal_scroll_maximum_at_980": captures.get("study-matrix-980x680-left.png",{}).get("scroll_maximum"),
        "all_columns_ordered": [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())],
        "scientific_validation": "NOT_CLAIMED",
        "captures": captures,
    }
    (out / "capture-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=True))
    window.close(); page.close(); app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
