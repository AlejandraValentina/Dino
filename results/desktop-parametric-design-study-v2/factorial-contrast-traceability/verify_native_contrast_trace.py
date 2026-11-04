from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QScrollArea
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.parametric_factorial_snapshot import import_parametric_factorial_csv_snapshot
from motorsim.desktop.results_page import _build_factorial_effects_csv, _write_factorial_effects_csv
from motorsim.desktop.services import new_design_project

OUT = Path(__file__).resolve().parent
EVIDENCE_DIR = OUT / "native-v4"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
CSV = EVIDENCE_DIR / "synthetic-factorial-snapshot.csv"
CAPTURE = EVIDENCE_DIR / "desktop-contrast-traceability.png"
RECEIPT = EVIDENCE_DIR / "native-receipt.json"
if any(path.exists() for path in (CSV, CAPTURE, RECEIPT)):
    raise SystemExit("Refusing to replace existing evidence")

app = QApplication.instance() or QApplication([])
app.setFont(QFont("Segoe UI", 9))
FIXTURE = EVIDENCE_DIR / "fixture"
FIXTURE.mkdir()
axes = [
    {"parameter": {"id": "A", "label": "Factor A", "unit": "mm"}, "values": [0.0, 1.0]},
    {"parameter": {"id": "B", "label": "Factor B", "unit": "cm3"}, "values": [10.0, 20.0]},
]
context = {"fuel_id": "synthetic-fuel", "afr_kg_air_per_kg_fuel": 12.5,
           "total_finite_volume_cells": 128, "cycles_requested": 5,
           "solver_identity_sha256": "synthetic-solver", "implementation_identity_sha256": "synthetic-impl"}
samples = [(0.0, 10.0, 10.0), (0.0, 20.0, 14.0), (1.0, 10.0, 20.0), (1.0, 20.0, 28.0)]
points, imported = [], []
for index, (a, b, power) in enumerate(samples):
    run_id = f"synthetic-factorial-source-{index}"
    identity = hashlib.sha256(f"synthetic-identity-{index}".encode()).hexdigest()
    result_dir = FIXTURE / f"run-{index}"
    result_dir.mkdir()
    result = {"schema": "DINO_ENGINEERING_RUN_V1", "status": "COMPLETE",
              "bindings": {"run_id": run_id, "identity_sha256": identity}}
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result_hash = hashlib.sha256(raw).hexdigest()
    (result_dir / "result.json").write_bytes(raw)
    (result_dir / "run.json").write_text(json.dumps({"result_sha256": result_hash}), encoding="utf-8")
    points.append({"index": index, "status": "COMPLETE", "run_id": run_id,
        "source_run_id": run_id, "rpm": 3000, "periodicity": "PERIOD_1",
        "classification": "PERIOD_1", "cycles_completed": 5,
        "factor_values": [{"parameter_id": "A", "value": a}, {"parameter_id": "B", "value": b}],
        "identity_sha256": identity, "engine_identity_sha256": identity,
        "result_sha256": result_hash, "result_artifact_sha256": result_hash,
        "run_directory": str(result_dir)})
    imported.append({"artifact_directory": str(result_dir), "run_id": run_id, "rpm": 3000,
        "result_sha256": result_hash, "identity_sha256": identity, "periodicity": "PERIOD_1",
        "classification": "PERIOD_1", "cycles_completed": 5, **context,
        "brake_power": power, "brake_power_status": "DEFINED",
        "brake_torque": power * 2, "brake_torque_status": "DEFINED",
        "BMEP": power * 3, "BMEP_status": "DEFINED"})
manifest = {"schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1", "design_method": "FACTORIAL_2X2_V1",
    "study_id": "synthetic-factorial-study", "project_id": "synthetic-factorial-project",
    "rpm": 3000, "baseline_engine_identity_sha256": "b" * 64, "factors": axes,
    "parameter": {"id": "factorial-2x2", "label": "2×2 · Factor A × Factor B",
        "axes": [axis["parameter"] for axis in axes]},
    "points": points, "scientific_validation": "NOT_CLAIMED"}
manifest_path = EVIDENCE_DIR / "synthetic-factorial.study.json"
manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")), encoding="utf-8")
digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
rows = _build_factorial_effects_csv(manifest_path, digest, manifest, imported)
_write_factorial_effects_csv(CSV, rows)
snapshot = import_parametric_factorial_csv_snapshot(CSV)
window = DinoDesktopWindow(new_design_project("SYNTHETIC factorial traceability"))
window.resize(1360, 900)
window.show()
window.analysis_mode.click()
page = window.results
page._show_parametric_factorial_csv_snapshot(snapshot, CSV)
page.factorial_csv_snapshot_contrasts.setCurrentCell(0, 0)
scroll = page.result_tabs.widget(3)
if isinstance(scroll, QScrollArea):
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
app.processEvents()
detail = page.factorial_csv_snapshot_detail.toPlainText()
first = snapshot["snapshot_contrasts"][0]
expected_ids = json.loads(first["contrast_source_run_ids_json"])
expected_hashes = json.loads(first["contrast_source_result_sha256s_json"])
if not window.grab().save(str(CAPTURE)):
    raise SystemExit("Desktop capture failed")
checks = {
    "fixture_origin": "synthetic; no solver execution",
    "visible_desktop": window.isVisible(),
    "selected_row": page.factorial_csv_snapshot_contrasts.currentRow(),
    "four_source_ids_visible": all(value in detail for value in expected_ids),
    "four_result_hashes_visible": all(value in detail for value in expected_hashes),
    "binding_status_visible": "MATCHES_POINT_ROWS" in detail,
    "read_only_snapshot": snapshot["snapshot"]["read_only"],
    "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
    "source_csv_sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
}
RECEIPT.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False))
if not all((checks["visible_desktop"], checks["four_source_ids_visible"],
            checks["four_result_hashes_visible"], checks["binding_status_visible"],
            checks["read_only_snapshot"])):
    raise SystemExit("Native Desktop contrast provenance check failed")
window.close()
app.quit()
