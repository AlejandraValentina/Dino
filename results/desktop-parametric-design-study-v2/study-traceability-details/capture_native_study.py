from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from PySide6.QtCore import QEventLoop, QTimer, QPoint
from PySide6.QtWidgets import QApplication

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.preferences import artifact_root
from motorsim.desktop.services import new_design_project
from motorsim.engine_configuration import identity
from motorsim.engine_project import validate_project


root = artifact_root()
manifest_path = (root / "design-studies-v1" / "synthetic-rpm-envelope-smoke-20261104" /
    "synthetic-rpm-envelope-smoke-20261104" / "rpm-envelope" / "study.json")
raw = manifest_path.read_bytes()
manifest = json.loads(raw.decode("utf-8"))
project = new_design_project(manifest["project_id"])
if identity(project["base_engine"]) != manifest["baseline_engine_identity_sha256"]:
    raise SystemExit("synthetic RPM study does not share the registered baseline")
project["study_references"].append({
    "path": str(manifest_path), "study_id": manifest["study_id"],
    "source_project_id": manifest["project_id"], "schema": manifest["schema"],
    "manifest_sha256": hashlib.sha256(raw).hexdigest(),
})
validate_project(project)

app = QApplication.instance() or QApplication([])
window = DinoDesktopWindow(project)
window.resize(1360, 900)
window.show()
app.processEvents()
window.set_workspace_mode(1)
app.processEvents()
page = window.results
page.open_project_study_button.click()
loop = QEventLoop()
poll = QTimer(); poll.setInterval(50)
def loaded():
    if page.dataset is not None and page.design_study_table.rowCount() == len(manifest["points"]):
        loop.quit()
poll.timeout.connect(loaded); poll.start()
QTimer.singleShot(60000, loop.quit)
loop.exec(); poll.stop(); app.processEvents()
if page.dataset is None or page.design_study_table.rowCount() != len(manifest["points"]):
    raise SystemExit("Desktop no pudo cargar los artifacts sintéticos guardados")
page.design_study_table.setCurrentCell(0, 0)
text = page.design_study_traceability.toPlainText()
for required in ("Coincide con el SHA registrado por el proyecto", "Verificado: hash coincide",
                 "Verificada: hash e identidad de la corrida coinciden", "Ciclos insuficientes"):
    if required not in text:
        raise SystemExit(f"falta evidencia de procedencia: {required}")
page.result_tabs.setCurrentIndex(3)
scroll = page.result_tabs.currentWidget(); content = scroll.widget(); bar = scroll.verticalScrollBar()
detail_y = page.design_study_traceability_group.mapTo(content, QPoint(0, 0)).y()
bar.setValue(max(0, detail_y - 8)); app.processEvents()
output = Path(__file__).resolve().parent
capture = output / "native-study-point-traceability.png"
if not window.grab().save(str(capture)):
    raise SystemExit("falló la captura de la procedencia en ventana Qt nativa")
receipt = {
    "window": "Dino Desktop source · native Windows Qt window",
    "window_size": [window.width(), window.height()],
    "fixture_origin": "Previously saved synthetic RPM-envelope artifacts; opened read-only; no solver run",
    "study_id": manifest["study_id"],
    "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    "points_loaded": page.design_study_table.rowCount(),
    "selected_point_details": text,
    "source_verification": "VERIFIED_HASH_AND_IDENTITY" if "Verificada: hash e identidad" in text else "NOT_VERIFIED",
    "nested_sweep_verification": "HASH_MATCH" if "Verificado: hash coincide" in text else "NOT_VERIFIED",
    "scientific_validation": manifest.get("scientific_validation", "NOT_CLAIMED"),
    "capture": str(capture),
    "capture_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
}
(output / "native-window-receipt.json").write_text(
    json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, ensure_ascii=False))
window.close(); app.processEvents()
