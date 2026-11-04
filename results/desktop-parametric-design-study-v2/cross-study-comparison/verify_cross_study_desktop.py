from __future__ import annotations
import hashlib,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.pop("QT_QPA_PLATFORM",None)
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from PySide6.QtCore import QEventLoop,QTimer
from PySide6.QtWidgets import QApplication,QDialog,QDialogButtonBox
from motorsim.desktop.preferences import artifact_root
from motorsim.desktop.services import new_design_project
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.results_page import _load_verified_study_comparison
from motorsim.engine_configuration import identity
from motorsim.engine_project import validate_project

rpm_manifest=(artifact_root()/"design-studies-v1"/"synthetic-rpm-envelope-smoke-20261104"/
    "synthetic-rpm-envelope-smoke-20261104"/"rpm-envelope"/"study.json")
artifact_root_for_factorial=Path(os.environ.get("DINO_ARTIFACT_ROOT",Path.home()/"Dino-artifacts"))
factorial_manifest=(artifact_root_for_factorial/"desktop-parametric-factorial-v1"/"design-studies-v1"/
    "synthetic-factorial-integration"/"synthetic-factorial-smoke-20261104"/"study.json")
refs=[]
for path in (rpm_manifest,factorial_manifest):
    raw=path.read_bytes();manifest=json.loads(raw)
    refs.append({"path":str(path),"study_id":manifest["study_id"],"source_project_id":manifest["project_id"],
        "schema":manifest["schema"],"manifest_sha256":hashlib.sha256(raw).hexdigest()})
project=new_design_project("synthetic-cross-study-desktop-20261104")
if identity(project["base_engine"])!=json.loads(rpm_manifest.read_text())["baseline_engine_identity_sha256"]:
    raise SystemExit("synthetic source projects do not share the registered baseline identity")
project["study_references"].extend(refs);validate_project(project)
app=QApplication.instance() or QApplication([])
window=DinoDesktopWindow(project);window.resize(1360,900);window.show();app.processEvents();window.set_workspace_mode(1);app.processEvents()
page=window.results
if page.project_study_selector.count()!=2 or not page.compare_studies_button.isEnabled():
    raise SystemExit("project study comparison action is not available")
def _accept_dialog(app):
    dialog=app.activeModalWidget()
    if isinstance(dialog,QDialog):
        buttons=dialog.findChild(QDialogButtonBox)
        if buttons:buttons.button(QDialogButtonBox.StandardButton.Ok).click()
QTimer.singleShot(300,lambda: _accept_dialog(app))
page.compare_project_studies()
loop=QEventLoop();poll=QTimer();poll.setInterval(50)
def finished():
    if page.study_comparison is not None or page.study_comparison_notice.text().startswith("Comparación rechazada"):
        loop.quit()
poll.timeout.connect(finished);poll.start();QTimer.singleShot(60000,loop.quit);loop.exec();poll.stop();app.processEvents()
comparison=page.study_comparison
if comparison is None:
    raise SystemExit(page.study_comparison_notice.text())
if (len(comparison["pairs"])!=8 or len(comparison["unpaired"])!=2 or
    any(point.get("periodicity")=="PERIOD_1" for study in comparison["studies"] for point in study["points"])):
    raise SystemExit("exact RPM/periodicity comparison did not preserve the expected source states")
if any(metric["delta"] is not None for pair in comparison["pairs"] for metric in pair["metrics"].values()):
    raise SystemExit("transient/missing metrics were presented as a direct performance difference")
page.result_tabs.setCurrentIndex(3);app.processEvents()
scroll=page.result_tabs.currentWidget()
if hasattr(scroll,"verticalScrollBar"):scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
app.processEvents()
evidence=Path("results/desktop-parametric-design-study-v2/cross-study-comparison")
evidence.mkdir(parents=True,exist_ok=True)
capture=evidence/"cross-study-comparison-desktop-real-window.png"
if not window.grab().save(str(capture)):raise SystemExit("native Desktop capture failed")
with tempfile.TemporaryDirectory(prefix="dino-study-report-") as temp:
    report=Path(temp)/"comparison.html"
    with patch("motorsim.desktop.results_page.QFileDialog.getSaveFileName",return_value=(str(report),"HTML")):
        if not page.export_study_comparison():raise SystemExit("Desktop study report export action failed")
    report_sha=hashlib.sha256(report.read_bytes()).hexdigest()
receipt={"window":"Dino Desktop source · native Windows platform","size":[window.width(),window.height()],
    "project_studies":page.project_study_selector.count(),"study_ids":[study["study_id"] for study in comparison["studies"]],
    "source_manifest_sha256":[study["manifest_sha256"] for study in comparison["studies"]],
    "common_baseline_sha256":comparison["baseline_engine_identity_sha256"],
    "source_points":[len(study["points"]) for study in comparison["studies"]],
    "exact_pairs":len(comparison["pairs"]),"unpaired_points":len(comparison["unpaired"]),
    "exact_pair_rpms":sorted({pair["rpm"] for pair in comparison["pairs"]}),
    "periodicity_states":sorted({point["periodicity"] for study in comparison["studies"] for point in study["points"]}),
    "defined_metric_deltas":sum(metric["delta"] is not None for pair in comparison["pairs"] for metric in pair["metrics"].values()),
    "table_rows":page.study_comparison_table.rowCount(),"report_sha256":report_sha,
    "capture":str(capture),"capture_sha256":hashlib.sha256(capture.read_bytes()).hexdigest(),
    "scientific_validation":"NOT_CLAIMED"}
(evidence/"native-window-receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,ensure_ascii=False))
window.close();app.processEvents()
