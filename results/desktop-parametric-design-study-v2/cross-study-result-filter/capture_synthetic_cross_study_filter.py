"""Capture the native Results comparison filter with display-only synthetic data."""
from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project


def main() -> int:
    output = Path(__file__).with_name("cross-study-filter-synthetic.png")
    app = QApplication.instance() or QApplication(sys.argv)
    page = ResultsPage(DesktopContext(new_design_project("synthetic-cross-study-filter-ui")))

    studies = [
        {"study_id": name, "manifest_path": f"SYNTHETIC/{name}.study.json",
         "manifest_sha256": digest * 64,
         "parameter": {"label": "Escape (fixture de presentación)"}}
        for name, digest in (("Diseño A", "a"), ("Diseño B", "b"))
    ]

    def point(run: str, rpm: int, power: float, periodicity: str = "PERIOD_1") -> dict:
        return {
            "index": rpm, "run_id": run, "source_run_id": run, "rpm": float(rpm),
            "status": "COMPLETE", "classification": periodicity, "periodicity": periodicity,
            "engine_identity_sha256": ("c" if run.endswith("A") else "d") * 64,
            "identity_sha256": ("e" if run.endswith("A") else "f") * 64,
            "result_sha256": "1" * 64, "result_artifact_sha256": "2" * 64,
            "metrics": {"brake_power": power, "brake_torque": None, "BMEP": None},
        }

    a = point("run-3000-A", 3000, 10.2)
    b = point("run-3000-B", 3000, 11.1)
    unpaired = point("run-4000-A", 4000, 12.5, "INSUFFICIENT_CYCLES")
    pair = {
        "study_a": "Diseño A", "point_a": a, "study_b": "Diseño B", "point_b": b,
        "rpm": 3000.0, "pairing": "EXACT_RPM_AND_OPERATING_CONTEXT",
        "metrics": {
            "brake_power": {"a": 10.2, "b": 11.1, "delta": 0.9},
            "brake_torque": {"a": None, "b": None, "delta": None},
            "BMEP": {"a": None, "b": None, "delta": None},
        },
    }
    comparison = {
        "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256": "9" * 64,
        "studies": studies,
        "pairs": [pair],
        "unpaired": [{"study_id": "Diseño A", "point": unpaired,
                      "reason": "Punto sin pareja compatible en Diseño B."}],
        "notice": "DATOS SINTÉTICOS DE PRESENTACIÓN. No son una predicción ni validación física.",
    }
    page._study_comparison_loaded(comparison)
    # The project study panel is normally shown when project references exist.
    # This display-only fixture has no persisted project, so expose that panel
    # explicitly to render the selected comparison section.
    page.design_study_group.show()
    page.resize(1600, 1020)
    tab_index = next(index for index in range(page.result_tabs.count())
                     if page.result_tabs.tabText(index) == "Comparar")
    page.result_tabs.setCurrentIndex(tab_index)
    compare_scroll = page.result_tabs.widget(tab_index)
    compare_scroll.ensureWidgetVisible(page.study_comparison_group)
    window = QMainWindow()
    window.setWindowTitle("Dino 2T — Comparar estudios · fixture sintético")
    window.setCentralWidget(page)
    window.resize(1600, 1020)
    window.show()
    app.processEvents()
    compare_scroll.ensureWidgetVisible(page.study_comparison_group)
    app.processEvents()
    if not window.grab().save(str(output)):
        raise RuntimeError(f"No se pudo guardar la captura en {output}")
    window.close()
    app.processEvents()
    print(f"capture={output}\nsize=1600x1020\nrows={page.study_comparison_table.rowCount()}\n"
          f"counter={page.cross_study_filter_count.text()}\nfixture=SYNTHETIC_NOT_VALIDATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
