"""Capture per-endpoint periodicity filters with a synthetic comparison only."""
from __future__ import annotations

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
    output = Path(__file__).with_name("cross-study-periodicity-synthetic.png")
    app = QApplication.instance() or QApplication(sys.argv)
    page = ResultsPage(DesktopContext(new_design_project("synthetic-periodicity-filter")))
    studies = [
        {"study_id": label, "manifest_path": f"SYNTHETIC/{label}.json",
         "manifest_sha256": digest * 64, "parameter": {"label": "Escape"}}
        for label, digest in (("Diseño A", "a"), ("Diseño B", "b"))
    ]

    def point(run_id: str, rpm: int, periodicity: str, identity: str) -> dict:
        periodic = periodicity == "PERIOD_1"
        return {
            "index": rpm, "run_id": run_id, "source_run_id": run_id, "rpm": float(rpm),
            "status": "COMPLETE", "classification": periodicity, "periodicity": periodicity,
            "engine_identity_sha256": identity * 64, "identity_sha256": identity.upper() * 64,
            "result_sha256": "c" * 64, "result_artifact_sha256": "d" * 64,
            "metrics": {"brake_power": 11.0 if periodic else None,
                        "brake_torque": None, "BMEP": None},
        }

    a = point("run-A-3000", 3000, "PERIOD_1", "e")
    b = point("run-B-3000", 3000, "INSUFFICIENT_CYCLES", "f")
    extra = point("run-A-4000", 4000, "NOT_EVALUATED", "e")
    comparison = {
        "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256": "9" * 64,
        "studies": studies,
        "pairs": [{"study_a": "Diseño A", "point_a": a, "study_b": "Diseño B",
                   "point_b": b, "rpm": 3000.0,
                   "pairing": "EXACT_RPM_AND_OPERATING_CONTEXT",
                   "metrics": {"brake_power": {"a": 11.0, "b": None, "delta": None},
                               "brake_torque": {"a": None, "b": None, "delta": None},
                               "BMEP": {"a": None, "b": None, "delta": None}}}],
        "unpaired": [{"study_id": "Diseño A", "point": extra,
                      "reason": "Fixture sintético: punto sin contraparte."}],
        "notice": "DATOS SINTÉTICOS DE PRESENTACIÓN; no constituyen validación física.",
    }
    page._study_comparison_loaded(comparison)
    page.design_study_group.show()
    page.cross_study_periodicity_a_filter.setCurrentIndex(
        page.cross_study_periodicity_a_filter.findData("PERIOD_1"))
    page.cross_study_periodicity_b_filter.setCurrentIndex(
        page.cross_study_periodicity_b_filter.findData("INSUFFICIENT_CYCLES"))
    page.resize(1600, 1020)
    comparison_group = page.study_comparison_group
    page.design_study_group.layout().removeWidget(comparison_group)
    comparison_group.setParent(None)
    window = QMainWindow()
    window.setWindowTitle("Dino 2T — periodicidad por extremo · sintético")
    window.setCentralWidget(comparison_group)
    window.resize(1600, 1020)
    window.show();app.processEvents()
    app.processEvents()
    if not window.grab().save(str(output)):
        raise RuntimeError(f"No se pudo guardar la captura: {output}")
    print(f"capture={output}\nrows={page.study_comparison_table.rowCount()}\n"
          f"visible={page.cross_study_filter_count.text()}\n"
          "fixture=SYNTHETIC_NOT_VALIDATION")
    window.close();app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
