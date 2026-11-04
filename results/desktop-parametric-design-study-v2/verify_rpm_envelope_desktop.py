from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
os.environ.pop("QT_QPA_PLATFORM",None)
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PySide6.QtCore import QEventLoop,QTimer
from PySide6.QtWidgets import QApplication
from motorsim.desktop.services import new_design_project
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.preferences import artifact_root

log=artifact_root()/"design-studies-v1"/"synthetic-rpm-envelope-smoke-20261104"/"synthetic-rpm-envelope-smoke-20261104"/"rpm-envelope"/"study.json"
raw=log.read_bytes();manifest=json.loads(raw)
project=new_design_project(manifest["project_id"])
project["study_references"].append({"path":str(log),"study_id":manifest["study_id"],
    "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
    "source_project_id":manifest["project_id"]})
from motorsim.engine_project import validate_project
validate_project(project)
app=QApplication.instance() or QApplication([])
window=DinoDesktopWindow(project);window.resize(1360,900);window.show();app.processEvents()
window.set_workspace_mode(1);app.processEvents()
page=window.results
if not page.open_selected_project_study():raise SystemExit(page.design_study_notice.text())
loop=QEventLoop();timer=QTimer();timer.setInterval(50)
def check():
    if page.dataset is not None or not page.path_label.text().startswith("Verificando artifacts EXPLORATORY"):
        loop.quit()
timer.timeout.connect(check);timer.start();QTimer.singleShot(60000,loop.quit);loop.exec();timer.stop();app.processEvents()
if page.dataset is None or len(page.dataset.get("points",[]))!=4:
    raise SystemExit(f"Desktop did not load four imported results: {page.path_label.text()}")
if page.design_study_table.rowCount()!=4 or page.design_response_plot.series:
    raise SystemExit("Desktop envelope result presentation failed")
if [page.design_study_table.item(index,0).text() for index in (2,3)]!=["Diseño 2","Diseño 2"]:
    raise SystemExit("Desktop did not group multiple RPM rows under the same design")
page.result_tabs.setCurrentIndex(3);app.processEvents()
scroll=page.result_tabs.currentWidget()
if hasattr(scroll,"verticalScrollBar"):scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
app.processEvents()
capture=Path("results/desktop-parametric-design-study-v2/rpm-envelope-smoke-desktop-real-window.png")
capture.parent.mkdir(parents=True,exist_ok=True)
if not window.grab().save(str(capture)):raise SystemExit("Desktop screenshot was not saved")
receipt={"window":"Dino Desktop source · native Windows platform","size":[window.width(),window.height()],
    "project_study_selector_count":page.project_study_selector.count(),"imported_points":len(page.dataset["points"]),
    "study_table_rows":page.design_study_table.rowCount(),"response_1d_suppressed":not page.design_response_plot.series,
    "periodicity_states":sorted({row.get("periodicity") for row in page.dataset["points"]}),
    "study_id":manifest["study_id"],"manifest_sha256":hashlib.sha256(raw).hexdigest(),
    "capture_sha256":hashlib.sha256(capture.read_bytes()).hexdigest(),
    "capture":str(capture)}
Path("results/desktop-parametric-design-study-v2/rpm-envelope-acceptance/desktop-window-receipt.json").write_text(
    json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2))
window.close();app.processEvents()
