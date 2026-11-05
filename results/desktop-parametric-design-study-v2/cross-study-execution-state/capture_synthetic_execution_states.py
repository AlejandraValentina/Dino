"""Capture execution/periodicity state filters with synthetic data only."""
from __future__ import annotations

import sys
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMainWindow

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project


def main() -> int:
    output_dir = Path(__file__).resolve().parent
    app = QApplication.instance() or QApplication(sys.argv)
    page = ResultsPage(DesktopContext(new_design_project("synthetic-periodicity-filter")))
    studies = [
        {"study_id": label, "manifest_path": f"SYNTHETIC/{label}.json",
         "manifest_sha256": digest * 64, "parameter": {"label": "Escape"}}
        for label, digest in (("Diseño A", "a"), ("Diseño B", "b"))
    ]

    def point(run_id: str, rpm: int, periodicity: str, identity: str,
              execution_status: str = "COMPLETE", classification: str | None = None) -> dict:
        periodic = periodicity == "PERIOD_1"
        return {
            "index": rpm, "run_id": run_id, "source_run_id": run_id, "rpm": float(rpm),
            "status": execution_status, "classification": classification or periodicity,
            "periodicity": periodicity,
            "engine_identity_sha256": identity * 64, "identity_sha256": identity.upper() * 64,
            "result_sha256": "c" * 64, "result_artifact_sha256": "d" * 64,
            "metrics": {"brake_power": 11.0 if periodic else None,
                        "brake_torque": None, "BMEP": None},
        }

    a = point("run-A-3000", 3000, "PERIOD_1", "e")
    b = point("run-B-3000", 3000, "INSUFFICIENT_CYCLES", "f",
              "COMPLETE", "MAX_CYCLES_NONCONVERGED")
    extra = point("run-A-4000", 4000, "NOT_EVALUATED", "e",
                  "CANCELLED_CHECKPOINTED", "NOT_EVALUATED")
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
    page.cross_study_execution_a_filter.setCurrentIndex(
        page.cross_study_execution_a_filter.findData("COMPLETE"))
    page.cross_study_execution_b_filter.setCurrentIndex(
        page.cross_study_execution_b_filter.findData("COMPLETE"))
    page.resize(1600, 1020)
    comparison_group = page.study_comparison_group
    page.design_study_group.layout().removeWidget(comparison_group)
    comparison_group.setParent(None)
    window = QMainWindow()
    window.setWindowTitle("Dino 2T — periodicidad por extremo · sintético")
    window.setCentralWidget(comparison_group)
    window.show();app.processEvents()
    captures={}
    for width,height,name in ((980,680,"cross-study-state-periodicity-980x680.png"),
                              (1360,900,"cross-study-execution-states-1360x900.png")):
        window.resize(width,height);app.processEvents();app.processEvents()
        output=output_dir/name
        if not window.grab().save(str(output)):
            raise RuntimeError(f"No se pudo guardar la captura: {output}")
        captures[output.name]={"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "bytes":output.stat().st_size,"width":width,"height":height}
    page._clear_cross_study_filters()
    page.cross_study_pair_filter.setCurrentIndex(page.cross_study_pair_filter.findData("unpaired"))
    page.cross_study_periodicity_a_filter.setCurrentIndex(
        page.cross_study_periodicity_a_filter.findData("NOT_EVALUATED"))
    page.cross_study_periodicity_b_filter.setCurrentIndex(
        page.cross_study_periodicity_b_filter.findText("Sin punto"))
    page.cross_study_execution_a_filter.setCurrentIndex(
        page.cross_study_execution_a_filter.findData("CANCELLED_CHECKPOINTED"))
    page.cross_study_execution_b_filter.setCurrentIndex(
        page.cross_study_execution_b_filter.findText("Sin punto"))
    window.resize(1600,1020);app.processEvents();app.processEvents()
    output=output_dir/"cross-study-cancelled-checkpoint-1600x1020.png"
    if not window.grab().save(str(output)):
        raise RuntimeError(f"No se pudo guardar la captura: {output}")
    captures[output.name]={"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes":output.stat().st_size,"width":1600,"height":1020}
    receipt={"schema":"DINO_SYNTHETIC_CROSS_STUDY_EXECUTION_STATE_CAPTURE_V1",
        "fixture_origin":"synthetic display/interaction only; no solver or scientific claim",
        "visible_rows":page.cross_study_filter_count.text(),"total_rows":page.study_comparison_table.rowCount(),
        "captures":captures}
    (output_dir/"capture-receipt.json").write_text(
        json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"rows={page.study_comparison_table.rowCount()}\n"
          f"visible={page.cross_study_filter_count.text()}\n"
          f"fixture=SYNTHETIC_NOT_VALIDATION\ncaptures={list(captures)}")
    window.close();app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
