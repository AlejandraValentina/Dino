from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project


def point(run_id: str, rpm: float, periodicity: str, power: float | None) -> dict:
    return {
        "index": int(rpm), "run_id": run_id, "rpm": rpm,
        "classification": periodicity, "periodicity": periodicity,
        "status": "COMPLETE", "metrics": {
            "brake_power": power,
            "brake_torque": None if power is None else power * 2,
            "BMEP": None,
        },
        "engine_identity_sha256": "a" * 64,
        "identity_sha256": "b" * 64,
        "result_sha256": "c" * 64,
        "result_artifact_sha256": "d" * 64,
    }


app = QApplication.instance() or QApplication([])
window = DinoDesktopWindow(new_design_project("synthetic-response-plot-ui-fixture"))
window.resize(1360, 900)
window.show()
app.processEvents()
window.set_workspace_mode(1)
app.processEvents()
page = window.results
a3, b3 = point("synthetic-a-3000", 3000, "PERIOD_1", 10.0), point("synthetic-b-3000", 3000, "PERIOD_1", 12.0)
a4, b4 = point("synthetic-a-4000", 4000, "PERIOD_1", 14.0), point("synthetic-b-4000", 4000, "INSUFFICIENT_CYCLES", None)

def pair(left, right, rpm):
    return {
        "study_a": "synthetic-study-A", "point_a": left,
        "study_b": "synthetic-study-B", "point_b": right,
        "rpm": float(rpm), "pairing": "EXACT_RPM_AND_OPERATING_CONTEXT",
    }

comparison = {
    "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
    "baseline_engine_identity_sha256": "e" * 64,
    "studies": [
        {"study_id": "synthetic-study-A", "manifest_path": "presentation-fixture-A.study.json",
         "manifest_sha256": "1" * 64, "parameter": {"label": "Escape (fixture)"}},
        {"study_id": "synthetic-study-B", "manifest_path": "presentation-fixture-B.study.json",
         "manifest_sha256": "2" * 64, "parameter": {"label": "Escape (fixture)"}},
    ],
    "pairs": [pair(a3, b3, 3000), pair(a4, b4, 4000)],
    "unpaired": [{"study_id": "synthetic-study-A",
        "point": point("synthetic-a-5000", 5000, "PERIOD_1", 16.0),
        "reason": "No existe un punto de otro estudio en la misma RPM exacta."}],
    "notice": "Fixture sintético de presentación; no es resultado del solver.",
}
for item in comparison["pairs"]:
    a, b = item["point_a"], item["point_b"]
    item["metrics"] = {
        metric: {"a": a["metrics"].get(metric), "b": b["metrics"].get(metric),
                 "delta": None}
        for metric in ("brake_power", "brake_torque", "BMEP")
    }

page._study_comparison_loaded(comparison)
page.design_study_group.show()  # presentation fixture has no persisted project study references
page.study_comparison_group.show()
page.study_comparison_notice.setText(
    "Fixture sintético sólo para verificar presentación. No procede del solver ni constituye evidencia física.")
page.result_tabs.setCurrentIndex(3)
compare_scroll = page.result_tabs.currentWidget()
compare_content = compare_scroll.widget()
scroll_bar = compare_scroll.verticalScrollBar()
plot_y = page.study_comparison_response_plot.mapTo(compare_content, QPoint(0, 0)).y()
scroll_bar.setValue(max(0, plot_y - 8))
app.processEvents()
output = Path(__file__).resolve().parent
plot_capture = output / "cross-study-response-plot-native-chart.png"
if not window.grab().save(str(plot_capture)):
    raise SystemExit("no se pudo guardar la captura nativa del gráfico")
scroll_bar.setValue(scroll_bar.maximum())
app.processEvents()
table_capture = output / "cross-study-response-plot-native-table.png"
if not window.grab().save(str(table_capture)):
    raise SystemExit("no se pudo guardar la captura nativa de la tabla")
receipt = {
    "window": "Dino Desktop source · native Windows Qt window",
    "size": [window.width(), window.height()],
    "fixture_origin": "synthetic presentation-only fixture; no solver execution or physical evidence",
    "metric": page.study_comparison_metric.currentData(),
    "plot_series": [{"name": series["name"], "points": series["points"],
                     "connect": series["connect"]}
                    for series in page.study_comparison_response_plot.series],
    "excluded_exact_pairs": 1,
    "table_rows_including_nonperiodic_and_unpaired": page.study_comparison_table.rowCount(),
    "captures": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                  for path in (plot_capture, table_capture)],
    "scientific_validation": "NOT_CLAIMED",
}
(output / "native-window-receipt.json").write_text(
    json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, ensure_ascii=False))
window.close()
app.processEvents()
