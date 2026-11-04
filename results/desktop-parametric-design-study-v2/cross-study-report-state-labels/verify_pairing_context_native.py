from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import shutil
import winreg
from PySide6.QtWidgets import QApplication, QFileDialog, QScrollArea

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

OUT=Path(__file__).resolve().parent
REPORT=OUT/"native-pairing-context-v1.html"
APP_CAPTURE=OUT/"native-desktop-export-v1.png"
HTML_CAPTURE=OUT/"chrome-pairing-context-v1.png"
RECEIPT=OUT/"native-pairing-context-receipt.json"
if any(path.exists() for path in (REPORT,APP_CAPTURE,HTML_CAPTURE,RECEIPT)):
    raise SystemExit("Refusing to replace an existing versioned evidence file")


def locate_chrome():
    found=shutil.which("chrome.exe")
    if found:return Path(found)
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive,r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                value,_=winreg.QueryValueEx(key,None)
                candidate=Path(value)
                if candidate.is_file():return candidate
        except OSError:continue
    raise RuntimeError("No se encontró Chrome para comprobar visualmente el informe HTML")


APP=QApplication.instance() or QApplication([])
project=new_design_project("SYNTHETIC cross-study report response plot")
baseline="9"*64
bindings={}
for study_id in ("synthetic-A","synthetic-B"):
    path=OUT/f"pairing-{study_id[-1]}-v1.study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":study_id,
        "project_id":project["project_id"],"baseline_engine_identity_sha256":baseline,
        "scientific_validation":"NOT_CLAIMED","points":[]}
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
    project["study_references"].append({"path":str(path),"study_id":study_id,
        "manifest_sha256":digest,"schema":manifest["schema"],"source_project_id":project["project_id"]})
    bindings[study_id]=(str(path),digest)


def point(index,run,rpm,periodicity,power,code):
    classification=("PERIOD_1" if periodicity=="PERIOD_1" else
        "MAX_CYCLES_NONCONVERGED" if periodicity=="INSUFFICIENT_CYCLES" else "NOT_STARTED")
    return {"index":index,"run_id":run,"source_run_id":run,"rpm":float(rpm),
        "value":38.4+index,"unit":"mm","status":"COMPLETE" if periodicity=="PERIOD_1" else classification,
        "classification":classification,"periodicity":periodicity,"cycles_completed":8,
        "source_verified":False,"engine_identity_sha256":code*64,"identity_sha256":code.upper()*64,
        "result_sha256":hashlib.sha256((run+" result").encode()).hexdigest(),
        "result_artifact_sha256":hashlib.sha256((run+" artifact").encode()).hexdigest(),
        "run_directory":f"SYNTHETIC/{run}","context":{
            "fuel_id":"synthetic-fuel","afr_kg_air_per_kg_fuel":12.5,
            "total_finite_volume_cells":176,"cycles_requested":8,
            "solver_identity_sha256":"synthetic-solver",
            "implementation_identity_sha256":"synthetic-impl"},
        "metrics":{"brake_power":power,"brake_torque":None,"BMEP":None}}


a0=point(0,"synthetic-A-3000",3000,"PERIOD_1",10.25,"a")
b0=point(0,"synthetic-B-3000",3000,"PERIOD_1",11.5,"b")
a1=point(1,"synthetic-A-4000",4000,"PERIOD_1",15.0,"c")
b1=point(1,"synthetic-B-4000",4000,"INSUFFICIENT_CYCLES",None,"d")
b2=point(2,"synthetic-B-5000",5000,"NOT_EVALUATED",None,"e")
b3=point(3,"synthetic-B-context-mismatch-4000",4000,"PERIOD_1",16.0,"f")
b3["context"]["total_finite_volume_cells"]=128
studies=[]
for study_id,points in (("synthetic-A",[a0,a1]),("synthetic-B",[b0,b1,b2,b3])):
    manifest_path,manifest_sha=bindings[study_id]
    studies.append({"study_id":study_id,"source_project_id":project["project_id"],
        "manifest_path":manifest_path,"manifest_sha256":manifest_sha,
        "baseline_engine_identity_sha256":baseline,"parameter":{"label":"Escape","unit":"mm"},
        "points":points})
comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
    "baseline_engine_identity_sha256":baseline,"scientific_validation":"NOT_CLAIMED",
    "notice":"Fixture sintético de demostración; ninguna corrida ni predicción física.","studies":studies,
    "pairs":[
        {"study_a":"synthetic-A","point_a":a0,"study_b":"synthetic-B","point_b":b0,
         "rpm":3000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
         "metrics":{"brake_power":{"a":10.25,"b":11.5,"delta":1.25}}},
        {"study_a":"synthetic-A","point_a":a1,"study_b":"synthetic-B","point_b":b1,
         "rpm":4000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
         "metrics":{"brake_power":{"a":15.0,"b":None,"delta":None}}}],
    "unpaired":[{"study_id":"synthetic-B","point":b2,
        "reason":"Fixture sintético: no hay endpoint compatible a 5000 RPM."},
        {"study_id":"synthetic-B","point":b3,
        "reason":"Condiciones informadas incompatibles: total_finite_volume_cells."}]}
window=DinoDesktopWindow(project);window.resize(1440,900);window.show();window.analysis_mode.click()
page=window.results;page.result_tabs.setCurrentIndex(3);page._study_comparison_loaded(comparison)
scroll=page.result_tabs.widget(3)
if isinstance(scroll,QScrollArea):scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
APP.processEvents()
QFileDialog.getSaveFileName=lambda *args:(str(REPORT),"HTML (*.html)")
page.export_study_comparison_button.click();APP.processEvents()
app_capture_ok=window.grab().save(str(APP_CAPTURE))
html=REPORT.read_text(encoding="utf-8")
required=("aria-label=\"Potencia de freno por RPM exacta\"", "Pares excluidos de esta gráfica",
    "Uno o ambos endpoints no están clasificados PERIOD_1.","no hay endpoint compatible a 5000 RPM.",
    "RPM exacta y contexto operativo coincidente",
    "Condiciones informadas incompatibles: cantidad de celdas de volumen finito.",
    '"pairing": "EXACT_RPM_AND_OPERATING_CONTEXT"',
    '"reason": "Condiciones informadas incompatibles: total_finite_volume_cells."',
    "NOT_CLAIMED","synthetic-A-3000","synthetic-B-3000")
if not all(token in html for token in required):raise SystemExit("El HTML exportado omitió campos de aceptación")
chrome=locate_chrome()
with tempfile.TemporaryDirectory(prefix="dino-cross-report-",ignore_cleanup_errors=True) as profile:
    subprocess.run([str(chrome),"--headless=new","--disable-gpu","--hide-scrollbars","--no-first-run",
        "--no-default-browser-check","--run-all-compositor-stages-before-draw","--virtual-time-budget=10000",
        "--window-size=1360,3000",f"--user-data-dir={profile}",f"--screenshot={HTML_CAPTURE}",REPORT.resolve().as_uri()],
        check=True,timeout=45,capture_output=True,text=True)
capture_ok=HTML_CAPTURE.is_file()
html_svg_count=html.count('<svg role="img"');marker_count=html.count('<circle class="observed-point"')
receipt={"schema":"DINO_NATIVE_CROSS_STUDY_REPORT_PLOT_V1","synthetic":True,
    "desktop_window_visible":window.isVisible(),"desktop_size":[window.width(),window.height()],
    "project_study_references":len(project["study_references"]),"html_report_path":str(REPORT.relative_to(ROOT)),
    "html_sha256":hashlib.sha256(REPORT.read_bytes()).hexdigest(),"html_svg_count":html_svg_count,
    "html_marker_count":marker_count,"no_interpolated_lines":"<polyline" not in html,
    "excluded_nonperiodic_pair_listed":"Pares excluidos de esta gráfica" in html and "synthetic-B-4000" in html,
    "unpaired_point_preserved":"no hay endpoint compatible a 5000 RPM." in html,
    "manifest_hashes_preserved":all(binding[1] in html for binding in bindings.values()),
    "pair_rule_label_translated":"RPM exacta y contexto operativo coincidente" in html,
    "unpaired_context_field_label_translated":"cantidad de celdas de volumen finito" in html,
    "raw_pair_and_context_codes_preserved_in_source_json":(
        '"pairing": "EXACT_RPM_AND_OPERATING_CONTEXT"' in html and
        '"reason": "Condiciones informadas incompatibles: total_finite_volume_cells."' in html),
    "not_claimed_preserved":"NOT_CLAIMED" in html,"synthetic_notice_preserved":"Fixture sintético" in html,
    "desktop_capture_saved":app_capture_ok,"browser_capture_saved":capture_ok,
    "browser_capture_sha256":hashlib.sha256(HTML_CAPTURE.read_bytes()).hexdigest() if capture_ok else None,
    "browser":"Chrome headless; renderer only; Desktop export action generated the HTML"}
RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,ensure_ascii=False))
points_table=html.split('<table class="points-table">',1)[1].split("</table>",1)[0]
headers=points_table.split("</thead>",1)[0]
receipt["summary_header_count"]=headers.count("<th>")
receipt["expandable_point_count"]=points_table.count('class="point-provenance"')
receipt["full_provenance_fields_preserved"]=all(value in points_table for value in (
    "Motor SHA-256","Corrida SHA-256","Resultado SHA-256","Artifact SHA-256",
    "Fuente verificada al cargar"))
RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if not all((receipt["summary_header_count"]==9,receipt["expandable_point_count"]==6,
    receipt["full_provenance_fields_preserved"],receipt["desktop_window_visible"],
    receipt["pair_rule_label_translated"],receipt["unpaired_context_field_label_translated"],
    receipt["raw_pair_and_context_codes_preserved_in_source_json"],
    html_svg_count==1,marker_count==2,
    receipt["no_interpolated_lines"],receipt["excluded_nonperiodic_pair_listed"],
    receipt["unpaired_point_preserved"],receipt["manifest_hashes_preserved"],
    receipt["not_claimed_preserved"],receipt["synthetic_notice_preserved"],app_capture_ok,capture_ok)):
    raise SystemExit("Native Desktop/HTML report acceptance failed")
APP.quit()


