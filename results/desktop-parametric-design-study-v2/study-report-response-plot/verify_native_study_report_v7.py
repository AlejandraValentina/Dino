from __future__ import annotations
import hashlib,json,shutil,subprocess,tempfile,winreg
from pathlib import Path
from PySide6.QtWidgets import QApplication,QFileDialog
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys_path=str(ROOT)
import sys
if sys_path not in sys.path:sys.path.insert(0,sys_path)
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project
REPORT=OUT/'native-study-response-v7.html';APP_IMAGE=OUT/'native-desktop-export-v7.png';BROWSER_IMAGE=OUT/'chrome-rendered-study-response-v7.png';RECEIPT=OUT/'native-study-report-v7-receipt.json'
if any(p.exists() for p in (REPORT,APP_IMAGE,BROWSER_IMAGE,RECEIPT)):raise SystemExit('Refusing to replace versioned evidence')
app=QApplication.instance() or QApplication([])
identity='c'*64
source_rows=[];study_points=[]
for i,(run_id,x,rpm,state,power,baseline) in enumerate((
 ('synthetic-study-base',10.0,3000,'PERIOD_1',10.0,True),
 ('synthetic-study-alt',20.0,3000,'PERIOD_1',15.0,False),
 ('synthetic-study-transient',30.0,3000,'INSUFFICIENT_CYCLES',None,False))):
 run_dir=OUT/f'{run_id}-v7';run_dir.mkdir()
 attempt=run_dir/'attempt-001';attempt.mkdir()
 diagnostic_raw=json.dumps({'cycles':[{'cycle':8}]},sort_keys=True,separators=(',',':')).encode()
 (attempt/'manifest.json').write_bytes(diagnostic_raw)
 result={'schema':'DINO_ENGINEERING_RUN_V1','status':'COMPLETE','attempt':'attempt-001',
   'diagnostic_manifest_sha256':hashlib.sha256(diagnostic_raw).hexdigest(),
   'bindings':{'run_id':run_id,'identity_sha256':identity}}
 raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();(run_dir/'result.json').write_bytes(raw)
 digest=hashlib.sha256(raw).hexdigest();(run_dir/'run.json').write_text(json.dumps({'result_sha256':digest}),encoding='utf-8')
 source_rows.append({'project_id':'synthetic-source','variant_id':run_id,'run_id':run_id,'point_id':run_id,'rpm':rpm,
   'classification':state,'periodicity':state,'audit_status':'NOT_PERFORMED','cycles_completed':8,
   'brake_power':power,'brake_power_status':'DEFINED' if power is not None else 'UNDEFINED',
   'brake_torque':None,'brake_torque_status':'UNDEFINED','BMEP':None,'BMEP_status':'UNDEFINED',
   'result_sha256':digest,'artifact_directory':str(run_dir)})
 study_points.append({'index':i,'value':x,'unit':'mm','rpm':rpm,'baseline':baseline,'status':'COMPLETE',
   'classification':state,'periodicity':state,'run_id':run_id,'source_run_id':run_id,'run_directory':str(run_dir),
   'identity_sha256':identity,'engine_identity_sha256':identity,'result_sha256':digest,'result_artifact_sha256':digest})
study_points.append({'index':3,'value':40.0,'unit':'mm','rpm':3000,'status':'NOT_STARTED','classification':'NOT_STARTED','periodicity':'NOT_EVALUATED'})
manifest={'schema':'DINO_PARAMETRIC_DESIGN_STUDY_V1','study_id':'SYNTHETIC-single-study-report-v7',
 'project_id':'synthetic-report-project','status':'PARTIAL','rpm':3000,'scientific_validation':'NOT_CLAIMED',
 'parameter':{'id':'exhaust:length','label':'Largo de escape','unit':'mm'},'points':study_points}
manifest_path=OUT/'synthetic-study-v7.study.json';manifest_path.write_text(json.dumps(manifest,sort_keys=True),encoding='utf-8')
manifest_hash=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
project=new_design_project('SYNTHETIC study report');project['study_references'].append({'path':str(manifest_path),'study_id':manifest['study_id'],
 'manifest_sha256':manifest_hash,'schema':manifest['schema'],'source_project_id':manifest['project_id']})
window=DinoDesktopWindow(project);window.resize(1360,900);window.show();window.analysis_mode.click();app.processEvents()
page=window.results;page.dataset={'schema':'DINO_DESKTOP_ENGINEERING_DATA_V1','points':source_rows,'experimental_validation':'NOT_CLAIMED',
 'provenance':'Synthetic report presentation fixture'};page.source_kind='EXPLORATORY';page.source=None
page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path;page.design_study_manifest_sha256=manifest_hash
page.design_study_reference={'path':str(manifest_path),'study_id':manifest['study_id'],'manifest_sha256':manifest_hash,'source_project_id':manifest['project_id']}
page.design_study_group.show();page.variants.clear()
for row in source_rows:page.variants.addItem(row['variant_id'])
for i in range(page.variants.count()):page.variants.item(i).setCheckState(__import__('PySide6').QtCore.Qt.CheckState.Checked)
QFileDialog.getSaveFileName=lambda *args:(str(REPORT),'HTML (*.html)')
page.export_report_button.click();app.processEvents()
if not REPORT.is_file():raise SystemExit('Desktop HTML export action did not create the report')
app_capture=window.grab().save(str(APP_IMAGE));html=REPORT.read_text(encoding='utf-8')
required=('Respuesta de freno por' if False else 'Potencia de freno por Largo de escape','Puntos excluidos de la respuesta','SYNTHETIC-single-study-report-v7','NOT_CLAIMED')
if not all(token in html for token in required):raise SystemExit('Exported report is missing acceptance content')
chrome=shutil.which('chrome.exe')
if not chrome:
 for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
  try:
   with winreg.OpenKey(hive,r'Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe') as key:
    chrome=winreg.QueryValueEx(key,None)[0];break
  except OSError:pass
if not chrome:raise RuntimeError('Chrome not found for report rendering')
with tempfile.TemporaryDirectory(prefix='dino-study-report-') as profile:
 subprocess.run([chrome,'--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run','--no-default-browser-check',
  '--run-all-compositor-stages-before-draw','--virtual-time-budget=10000','--window-size=1360,2400',
  f'--user-data-dir={profile}',f'--screenshot={BROWSER_IMAGE}',REPORT.resolve().as_uri()],check=True,timeout=45,capture_output=True,text=True)
receipt={'schema':'DINO_NATIVE_SINGLE_STUDY_REPORT_RESPONSE_V1','synthetic':True,'desktop_visible':window.isVisible(),
 'desktop_size':[window.width(),window.height()],'report_path':str(REPORT.relative_to(ROOT)),
 'report_sha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),'manifest_sha256':manifest_hash,
 'plotted_marker_count':html.count('class="observed-point"'),'svg_count':html.count('<svg role="img"'),
 'nonperiodic_exclusion_visible':'fuente está clasificada Ciclos insuficientes' in html,
 'unstarted_point_exclusion_visible':'Punto sin resultado terminal: No iniciada.' in html,
 'raw_state_codes_preserved_in_json':'\"status\": \"NOT_STARTED\"' in html and '\"periodicity\": \"INSUFFICIENT_CYCLES\"' in html,'unconnected_markers':'<polyline' not in html,
 'not_claimed_preserved':'NOT_CLAIMED' in html,'tamper_guard_tested':'tests/test_desktop_technical_report.py::test_single_study_report_plots_only_hash_bound_period_one_sources',
 'desktop_capture_saved':app_capture,'browser_capture_sha256':hashlib.sha256(BROWSER_IMAGE.read_bytes()).hexdigest(),
 'renderer':'Chrome headless; actual HTML created by Desktop export action'}
RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False))
if not all((receipt['synthetic'],receipt['desktop_visible'],receipt['plotted_marker_count']==2,receipt['svg_count']==2,
 receipt['nonperiodic_exclusion_visible'],receipt['unstarted_point_exclusion_visible'],receipt['raw_state_codes_preserved_in_json'],receipt['unconnected_markers'],receipt['not_claimed_preserved'],app_capture)):
 raise SystemExit('Native single-study report acceptance failed')
app.quit()
