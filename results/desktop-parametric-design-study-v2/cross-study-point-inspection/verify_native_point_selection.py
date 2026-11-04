from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

OUT=Path(__file__).resolve().parent
CAPTURE=OUT/"native-marker-selection-synthetic.png"
PLOT_CAPTURE=OUT/"native-response-plot-synthetic.png"
RECEIPT=OUT/"native-marker-selection-receipt.json"
APP=QApplication.instance() or QApplication([])
project=new_design_project("SYNTHETIC cross-study marker selection")
for study_id in ("synthetic-A","synthetic-B"):
    manifest_path=OUT/f"{study_id}.study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":study_id,
        "project_id":project["project_id"],"baseline_engine_identity_sha256":"9"*64,
        "scientific_validation":"NOT_CLAIMED","points":[]}
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(raw)
    project["study_references"].append({"path":str(manifest_path),"study_id":study_id,
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":project["project_id"]})
window=DinoDesktopWindow(project)
window.resize(1440,900)
window.show()
window.analysis_mode.click()
page=window.results
page.result_tabs.setCurrentIndex(3)


def point(index,run_id,rpm,periodicity,metric,code):
    return {"index":index,"run_id":run_id,"source_run_id":run_id+"-source","rpm":float(rpm),
        "value":38.123456789+index,"unit":"mm","status":"COMPLETE" if periodicity=="PERIOD_1" else "NOT_STARTED",
        "classification":"PERIOD_1" if periodicity=="PERIOD_1" else "NOT_STARTED",
        "periodicity":periodicity,"cycles_completed":5 if periodicity=="PERIOD_1" else 0,
        "metrics":{"brake_power":metric,"brake_torque":None,"BMEP":None},
        "engine_identity_sha256":code*64,"identity_sha256":code.upper()*64,
        "result_sha256":hashlib.sha256((run_id+"-result").encode()).hexdigest(),
        "result_artifact_sha256":hashlib.sha256((run_id+"-artifact").encode()).hexdigest(),
        "run_directory":f"SYNTHETIC/{run_id}","source_verified":False,
        "context":{"afr":12.5,"load":1.0}}


a=point(0,"synthetic-A0",3000,"PERIOD_1",10.25,"a")
b=point(0,"synthetic-B0",3000,"PERIOD_1",11.5,"b")
b_unpaired=point(1,"synthetic-B1",4000,"NOT_EVALUATED",None,"c")
comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
    "baseline_engine_identity_sha256":"9"*64,"scientific_validation":"NOT_CLAIMED",
    "notice":"Fixture sintético de interacción; no es una corrida ni validación.",
    "studies":[{"study_id":"synthetic-A","manifest_path":"SYNTHETIC/A.study.json",
        "manifest_sha256":"d"*64,"parameter":{"label":"Escape"}},
        {"study_id":"synthetic-B","manifest_path":"SYNTHETIC/B.study.json",
         "manifest_sha256":"e"*64,"parameter":{"label":"Escape"}}],
    "pairs":[{"study_a":"synthetic-A","point_a":a,"study_b":"synthetic-B","point_b":b,
        "rpm":3000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
        "metrics":{"brake_power":{"a":10.25,"b":11.5,"delta":1.25},
            "brake_torque":{"a":None,"b":None,"delta":None},
            "BMEP":{"a":None,"b":None,"delta":None}}}],
    "unpaired":[{"study_id":"synthetic-B","point":b_unpaired,
        "reason":"Fixture sintético: sin punto compatible a 4000 RPM."}]}
page._study_comparison_loaded(comparison)
APP.processEvents()
scroll=page.result_tabs.widget(3)
if isinstance(scroll,QScrollArea):
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    APP.processEvents()
plot=page.study_comparison_response_plot
marker=next(item for series in plot.series if series["name"]=="synthetic-B" for item in series["points"])
plot_y=plot.mapTo(scroll.widget(),QPoint(0,0)).y()
scroll.verticalScrollBar().setValue(max(0,plot_y-20))
APP.processEvents()
plot_capture_ok=window.grab().save(str(PLOT_CAPTURE))
plot_visible=plot.visibleRegion().boundingRect().height()>=plot.height()-4
all_points=plot._points();xmin,xmax,ymin,ymax=plot._axis_ranges(all_points)
rect=plot.rect().adjusted(76,18,-18,-40)
x=rect.left()+(marker["rpm"]-xmin)/(xmax-xmin)*rect.width()
y=rect.bottom()-(marker["value"]-ymin)/(ymax-ymin)*rect.height()
QTest.mouseClick(plot,Qt.MouseButton.LeftButton,pos=QPoint(round(x),round(y)))
APP.processEvents()
details=page.study_comparison_point_details.toPlainText()
item=page.study_comparison_table.currentItem()
selected_row=(item.data(Qt.ItemDataRole.UserRole) if item else None)
scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
APP.processEvents()
capture_ok=window.grab().save(str(CAPTURE))
receipt={"schema":"DINO_NATIVE_CROSS_STUDY_POINT_SELECTION_V1","synthetic":True,
    "visible_native_window":window.isVisible(),"window_size":[window.width(),window.height()],
    "clicked_series":marker["comparison_study_id"],"clicked_run_id":marker["comparison_run_id"],
    "exact_comparison_rows":marker["comparison_rows"],"selected_pair_index":selected_row,
    "click_target_visible_before_click":plot_visible,"plot_capture_saved":plot_capture_ok,
    "source_status_shown_unverified":"No verificada al cargar la comparación" in details,
    "selected_source_run_shown":"synthetic-B0-source" in details,
    "manifest_hash_shown":"e"*64 in details,
    "artifact_hash_shown":b["result_artifact_sha256"] in details,
    "unpaired_row_still_present":page.study_comparison_table.rowCount()==2,
    "comparison_group_visible":page.study_comparison_group.isVisible(),
    "normal_curves_not_used":page.plot.series==[],"capture_saved":capture_ok,
    "capture_sha256":hashlib.sha256(CAPTURE.read_bytes()).hexdigest() if capture_ok else None,
    "plot_capture_sha256":hashlib.sha256(PLOT_CAPTURE.read_bytes()).hexdigest() if plot_capture_ok else None}
RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,ensure_ascii=False))
if not all((receipt["visible_native_window"],receipt["source_status_shown_unverified"],
        receipt["selected_source_run_shown"],receipt["manifest_hash_shown"],receipt["artifact_hash_shown"],
        receipt["unpaired_row_still_present"],receipt["comparison_group_visible"],
        receipt["normal_curves_not_used"],receipt["click_target_visible_before_click"],
        plot_capture_ok,capture_ok)) or selected_row!=0:
    raise SystemExit("Native point selection acceptance failed")
APP.quit()
