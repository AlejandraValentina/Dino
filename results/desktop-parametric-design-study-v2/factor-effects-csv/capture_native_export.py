from __future__ import annotations
import csv, hashlib, importlib.util, json, sys
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
app=QApplication([])
repo=Path.cwd();sys.path.insert(0,str(repo))
spec=importlib.util.spec_from_file_location('desktop_design_study_tests',repo/'tests/test_desktop_design_study.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project
base=repo/'results/desktop-parametric-design-study-v2/factor-effects-csv'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
run=base/f'native-smoke-{stamp}';run.mkdir(parents=True)
sources=run/'sources';sources.mkdir()
manifest,points=module._factorial_effect_fixture(sources)
manifest['study_id']=f'factorial-export-synthetic-{stamp}'
manifest_path=run/'synthetic-factorial.study.json'
raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();manifest_path.write_bytes(raw)
digest=hashlib.sha256(raw).hexdigest()
project=DesktopContext(new_design_project(f'SYNTHETIC factorial CSV {stamp}'))
project.project['study_references']=[{'path':str(manifest_path),'study_id':manifest['study_id'],'manifest_sha256':digest}]
page=ResultsPage(project);page.resize(1480,900);page.dataset={'schema':'DINO_EXPLORATORY_COMPARISON_V1','experimental_validation':'NOT_PERFORMED','points':points}
page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
page._update_design_study_summary();page.result_tabs.setCurrentIndex(3)
out=run/'factorial-export.csv';warnings=[]
QFileDialog.getSaveFileName=lambda *args:(str(out),'CSV (*.csv)')
QMessageBox.warning=lambda *args:warnings.append(str(args[2]))
page.show();app.processEvents()
def verify_and_capture():
    page.result_tabs.widget(3).verticalScrollBar().setValue(page.result_tabs.widget(3).verticalScrollBar().maximum())
    page.export_factorial_effects_button.click();app.processEvents()
    if not out.is_file() or warnings:raise RuntimeError(f'Export action failed: {warnings}')
    with out.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    point_rows=[row for row in rows if row['record_type']=='POINT']
    contrast_rows=[row for row in rows if row['record_type']=='CONTRAST']
    if len(point_rows)!=4 or len(contrast_rows)!=9:raise RuntimeError('Unexpected CSV record counts')
    if any(row['source_verified']!='True' for row in point_rows):raise RuntimeError('A point source was not verified')
    if any(row['scientific_validation']!='NOT_CLAIMED' for row in rows):raise RuntimeError('Scientific qualification changed')
    shot=run/'factorial-csv-native-window.png'
    if not page.grab().save(str(shot)):raise RuntimeError('Native screenshot could not be saved')
    receipt={'evidence_type':'NATIVE_WINDOWS_QT_FACTORIAL_EXPORT_SYNTHETIC','platform':app.platformName(),
      'window_size':[page.width(),page.height()],'window_visible':page.isVisible(),'synthetic_only':True,
      'solver_invoked':False,'manifest':str(manifest_path),'manifest_sha256':digest,
      'csv':str(out),'csv_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'csv_schema':rows[0]['csv_schema'],'point_rows':len(point_rows),'contrast_rows':len(contrast_rows),
      'point_source_verification':[row['source_verified'] for row in point_rows],
      'nonperiodic_records':sum(row['contrast_status']=='UNAVAILABLE' for row in contrast_rows),
      'capture':str(shot),'capture_sha256':hashlib.sha256(shot.read_bytes()).hexdigest(),
      'notice':page.design_study_notice.text()}
    (run/'native-window-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    page.close();app.quit()
QTimer.singleShot(1200,verify_and_capture)
app.exec()
