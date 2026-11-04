from __future__ import annotations
import hashlib, importlib.util, json, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))
from PySide6.QtWidgets import QApplication
app = QApplication([])
spec = importlib.util.spec_from_file_location('desktop_design_study_tests', Path('tests/test_desktop_design_study.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project
out = Path('results/desktop-parametric-design-study-v2/factor-effects')
out.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory(prefix='dino-factorial-ui-synthetic-')
manifest, points = module._factorial_effect_fixture(Path(tmp.name))
page = ResultsPage(DesktopContext(new_design_project('SINTÉTICO · efectos factoriales')))
page.design_study_manifest = manifest
page.design_study_manifest_path = out / 'synthetic-factorial.study.json'
page.dataset = {'schema':'DINO_EXPLORATORY_COMPARISON_V1','experimental_validation':'NOT_PERFORMED','points':points}
page.resize(1480, 900)
page._update_design_study_summary()
page.result_tabs.setCurrentIndex(3)
page.show()
app.processEvents()
receipts=[]
def capture_state(path, state):
    study_scroll = page.result_tabs.widget(3)
    study_scroll.verticalScrollBar().setValue(study_scroll.verticalScrollBar().maximum())
    app.processEvents()
    ok = page.grab().save(str(path))
    receipt={'platform':app.platformName(),'window_size':[page.width(),page.height()],
        'visible':page.isVisible(),'capture_saved':ok,'capture':str(path),
        'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'matrix_rows':page.design_study_table.rowCount(),'effect_rows':page.factor_effects_table.rowCount(),
        'effect_values':[page.factor_effects_table.item(i,2).text() for i in range(page.factor_effects_table.rowCount())],
        'notice':page.factor_effects_notice.text(),'state':state,'synthetic':True}
    receipts.append(receipt)
    print(json.dumps(receipt,ensure_ascii=False))
def capture():
    capture_state(out / 'factor-effects-native-available-synthetic.png', 'four PERIOD_1 points')
    points[-1]['periodicity'] = 'INSUFFICIENT_CYCLES'
    points[-1]['classification'] = 'MAX_CYCLES_NONCONVERGED'
    manifest['points'][-1]['periodicity'] = 'INSUFFICIENT_CYCLES'
    manifest['points'][-1]['classification'] = 'MAX_CYCLES_NONCONVERGED'
    page.dataset = {'schema':'DINO_EXPLORATORY_COMPARISON_V1','experimental_validation':'NOT_PERFORMED','points':points}
    page._update_design_study_summary()
    app.processEvents()
    capture_state(out / 'factor-effects-native-nonperiodic-synthetic.png', 'one nonperiodic point')
    (out / 'native-window-receipt.json').write_text(
        json.dumps({'evidence_type':'NATIVE_WINDOWS_QT_PRESENTATION_SYNTHETIC',
            'evidence_qualification':'No solver execution or scientific validation; source artifacts are test fixtures.',
            'captures':receipts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    page.close()
    app.quit()
from PySide6.QtCore import QTimer
QTimer.singleShot(1600, capture)
app.exec()
tmp.cleanup()
