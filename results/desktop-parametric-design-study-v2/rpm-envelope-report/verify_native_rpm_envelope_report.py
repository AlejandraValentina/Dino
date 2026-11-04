from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QScrollArea

ARTIFACTS = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.services import new_design_project
from motorsim.desktop.preferences import artifact_root
from motorsim.engine_project import save_project

APP = QApplication.instance() or QApplication([])
manifest_path = (Path(artifact_root()) / "design-studies-v1" / "synthetic-rpm-envelope-smoke-20261104" /
                 "synthetic-rpm-envelope-smoke-20261104" / "rpm-envelope" / "study.json")
manifest_raw = manifest_path.read_bytes()
manifest_hash = hashlib.sha256(manifest_raw).hexdigest()
manifest = json.loads(manifest_raw)
project = new_design_project(manifest["project_id"])
study_reference = {"path": str(manifest_path), "study_id": manifest["study_id"],
    "source_project_id": manifest["project_id"], "schema": manifest["schema"],
    "manifest_sha256": manifest_hash}
project.setdefault("study_references", []).append(study_reference)
context = DesktopContext(project)
window = DinoDesktopWindow(context.project)
window.resize(1440, 900)
window.show()
window.analysis_mode.click()
page = window.results
page.result_tabs.setCurrentIndex(3)
destination = ARTIFACTS / "synthetic-rpm-envelope-report.html"
QFileDialog.getSaveFileName = lambda *args: (str(destination), "Informe HTML (*.html)")
receipt = {"schema": "DINO_NATIVE_RPM_ENVELOPE_REPORT_CHECK_V1", "source_kind": "SYNTHETIC",
    "solver_invocations": 0, "manifest_path": str(manifest_path), "manifest_sha256": manifest_hash}
project_path = ARTIFACTS / "synthetic-envelope-report-project.dino2t.json"
save_project(project_path, context.project)
window.context.path = project_path


def finish_if_loaded():
    points = (page.dataset or {}).get("points", []) if page.dataset else []
    if len(points) < len(manifest.get("points", [])):
        QTimer.singleShot(250, finish_if_loaded)
        return
    scroll=page.result_tabs.widget(3)
    if isinstance(scroll,QScrollArea):scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    APP.processEvents()
    report_ok = page.export_technical_report()
    APP.processEvents()
    screenshot = ARTIFACTS / "native-rpm-envelope-report.png"
    window.grab().save(str(screenshot))
    report_raw = destination.read_bytes()
    receipt.update({
        "native_window_visible": window.isVisible(), "outer_size": [window.width(), window.height()],
        "study_opened_from_project_reference": True, "loaded_points": len(points),
        "all_points_nonconverged": all(p.get("periodicity") == "INSUFFICIENT_CYCLES" for p in manifest["points"]),
        "report_export_action_succeeded": report_ok,
        "report_sha256": hashlib.sha256(report_raw).hexdigest(),
        "report_has_exact_grid_and_states": (b"RPM_ENVELOPE_V1" in report_raw and
            b"3000" in report_raw and b"4000" in report_raw and b"INSUFFICIENT_CYCLES" in report_raw),
        "screenshot": screenshot.name,
        "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
    })
    (ARTIFACTS / "native-window-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    window.close()
    APP.quit()


def open_study():
    opened = page.open_selected_project_study()
    if not opened:
        receipt["open_error"] = page.design_study_notice.text()
        (ARTIFACTS / "native-window-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        window.close();APP.quit();return
    QTimer.singleShot(250, finish_if_loaded)


QTimer.singleShot(1000, open_study)
APP.exec()
