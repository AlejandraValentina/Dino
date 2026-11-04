from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
app=QApplication([])
repo=Path.cwd();sys.path.insert(0,str(repo))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project
source=repo/'results/desktop-parametric-design-study-v2/study-data-export/synthetic-native-selected.csv'
out=repo/'results/desktop-parametric-design-study-v2/study-csv-reimport'
window=DinoDesktopWindow(new_design_project('SYNTHETIC study CSV read-only reimport'))
window.resize(1360,900);window.set_workspace_mode(1);window.show();app.processEvents()
window.results.load(source)
tries={'n':0}
def poll():
    tries['n']+=1
    page=window.results
    if getattr(page,'source_kind',None)=='PARAMETRIC_STUDY_CSV_SNAPSHOT':
        page.result_tabs.setCurrentIndex(3);app.processEvents()
        shot=out/'native-study-csv-snapshot-v2.png'
        if not window.grab().save(str(shot)):raise RuntimeError('native Desktop capture failed')
        points=page.dataset['snapshot_points']
        receipt={'evidence_type':'NATIVE_WINDOWS_QT_PARAMETRIC_CSV_SNAPSHOT_SYNTHETIC',
          'synthetic_only':True,'solver_invoked':False,'platform':app.platformName(),
          'window_visible':window.isVisible(),'window_size':[window.width(),window.height()],
          'source_csv':str(source),'source_csv_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'snapshot_schema':page.dataset['schema'],'study_id':page.dataset['snapshot']['study_id'],
          'point_count':page.study_csv_snapshot_table.rowCount(),
          'periodicity':[p.get('periodicity') for p in points],
          'source_verification_at_export':[p.get('source_verification') for p in points],
          'metrics':[p.get('brake_power_kw') for p in points],
          'imported_snapshot_sha256':page.dataset['snapshot']['csv_sha256'],
          'capture':str(shot),'capture_sha256':hashlib.sha256(shot.read_bytes()).hexdigest(),
          'notice':page.study_csv_snapshot_notice.text()}
        (out/'native-window-receipt-v2.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(receipt,ensure_ascii=False));window.close();app.quit();return
    if tries['n']>80:
        raise RuntimeError(f'load did not complete: loading={page.loading}, path={page.path_label.text()}')
    QTimer.singleShot(100,poll)
QTimer.singleShot(250,poll)
app.exec()
