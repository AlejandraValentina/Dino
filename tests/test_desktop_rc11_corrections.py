"""Presentation regressions using synthetic inputs; no physical campaigns."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import json
from pathlib import Path
import desktop_qsettings_isolation
from PySide6.QtCore import Qt,QPoint
from PySide6.QtWidgets import QApplication,QListWidgetItem,QScrollArea
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project,load_results
from motorsim.desktop.presentation import state_label
from motorsim.desktop.performance_curves import PowerCurvePanel
from motorsim.engine_project import save_project,load_project

APP=QApplication.instance() or QApplication([])

def window():
    w=DinoDesktopWindow(new_design_project());w.resize(960,630);w.show();APP.processEvents();return w

def close(w):
    w.context.dirty=False;w.close();APP.processEvents()

def test_exhaust_reopen_and_compact_history_do_not_hide_geometry(tmp_path):
    w=window();path=tmp_path/'synthetic.json';save_project(path,w.context.project)
    original=deepcopy(w.context.project['base_engine']['native_configuration'])
    w.context.replace_project(load_project(path),path)
    w.model_selector.setCurrentIndex(w.model_selector.findData(2));p=w.pages[1];p.view_tabs.setCurrentIndex(1)
    w._toggle_explorer();APP.processEvents()
    assert w.explorer_dock.isFloating()
    assert p.table.rowCount()==7 and p.table.viewport().height()>=90
    assert p.table.item(0,1).text()=='83.0'
    assert load_project(path)['base_engine']['native_configuration']==original
    w.explorer_dock.hide();close(w)

def test_engine_numbers_are_paint_only_and_essential_columns_are_visible():
    w=window();p=w.pages[0];native=deepcopy(w.context.engine()['native_configuration'])
    before=deepcopy(native['port_binding']['port_set'])
    p._edited_ports(native)
    assert native['port_binding']['port_set']==before
    for col in (4,5):assert not p.ports.isColumnHidden(col)
    item=p.ports.item(1,2);delegate=p.ports.itemDelegateForColumn(2)
    assert len(delegate.displayText(item.text(),p.locale()))<=8
    assert 'ID:' in p.ports.item(1,0).toolTip()
    assert p.ports.item(1,0).data(Qt.ItemDataRole.UserRole)=='primary-window'
    close(w)

def test_pair_conditions_ignore_changes_between_different_rpms():
    w=window();p=w.results
    rows=[dict(variant_id=name,rpm=rpm,fuel_id=str(rpm),point_configuration_sha256=name) for name in ('A','B') for rpm in (3000,3500)]
    p.dataset={'points':rows};p.variants.blockSignals(True);p.variants.clear()
    for name in ('A','B'):
        item=QListWidgetItem(name);item.setCheckState(Qt.CheckState.Checked);p.variants.addItem(item)
    p.variants.blockSignals(False);p._update_condition_notice()
    assert 'Configuraciones distintas' in p.condition_notice.text()
    assert 'combustible' not in p.condition_notice.text()
    rows[-1]['fuel_id']='different';p._update_condition_notice();assert 'combustible' in p.condition_notice.text()
    close(w)

def test_transients_default_off_and_never_produce_performance_maxima():
    panel=PowerCurvePanel();row=dict(variant_id='A',rpm=3000,mode='ENGINEERING_EXPLORATORY',classification='MAX_CYCLES_NONCONVERGED',periodicity='INSUFFICIENT_CYCLES',brake_power_status='UNDEFINED',brake_torque_status='UNDEFINED',transient_estimates=dict(brake_power=3,brake_torque=4))
    panel.set_dataset({'points':[row]}, {'A'})
    assert not panel.exploratory_toggle.isChecked() and panel.rows[0]['power'] is None
    assert 'MAX_CYCLES' not in panel.points.item(0,2).text()
    panel.exploratory_toggle.setChecked(True)
    assert panel.rows[0]['power'] is not None
    assert 'sin valores definidos' in panel.peaks.text()
    assert 'excluidos' in panel.peaks.text()
    assert row['classification']=='MAX_CYCLES_NONCONVERGED'
    panel.close()

def test_primary_metrics_visible_and_results_have_no_outer_scroll():
    w=window();w.set_workspace_mode(1);APP.processEvents()
    assert w.results.parent() is w.analysis_splitter
    assert all(card.isVisible() for card in w.results.metric_cards)
    assert w.strip_more.isVisible() and w.strip_cancel.isVisible()
    assert w.strip_more.mapTo(w,QPoint()).x()+w.strip_more.width()<=w.width()
    assert state_label('TERMINADA · MAX_CYCLES_NONCONVERGED')=='TERMINADA · Límite de ciclos · no convergida'
    w.pages[3].checkpoint_summary='4 puntos · EXPLORATORY_CURVE_PARTIAL'
    w._update_strip()
    assert 'EXPLORATORY_CURVE_PARTIAL' not in w.checkpoint_state.text()
    assert 'EXPLORATORY_CURVE_PARTIAL' in w.checkpoint_state.toolTip()
    close(w)

def test_historical_csv_companion_preserves_exact_thirty_points():
    root=Path(__file__).resolve().parents[1]/'results/desktop-windows-rc10-integrated'
    data=load_results(root/'packaged-historical.csv')
    source=json.loads((root/'packaged-historical.json').read_text(encoding='utf-8'))
    assert len(data['points'])==30 and data['points']==source['points']
    assert data['units']==source['units']

def test_missing_geometry_is_explained_without_mutating_or_leaving_stale_rows():
    from unittest.mock import patch
    w=window();p=w.pages[1];before=deepcopy(w.context.project)
    with patch('motorsim.desktop.exhaust_page.escape_sections',side_effect=ValueError('unidentified')):
        p.refresh()
    assert p.availability.text().startswith('Geometría de escape no disponible')
    assert p.table.rowCount()==0 and not p.profile.sections
    assert not p.table.signalsBlocked() and not p.apply_button.isEnabled()
    assert w.context.project==before
    p.refresh();assert p.table.rowCount()==7 and p.apply_button.isEnabled()
    close(w)

def test_exhaust_save_without_edit_preserves_full_precision_and_identity(tmp_path):
    from motorsim.engine_variants import escape_sections,stretch_partitioned_escape
    from motorsim.engine_configuration import identity
    w=window();p=w.pages[1];sections=escape_sections(w.context.engine())
    sections[0]['length_mm']=83.123456789
    precise=stretch_partitioned_escape(w.context.engine(),sections)
    precise['display_name']='precision-synthetic'
    w.context.replace_engine(precise,variant_name='precision-synthetic')
    w.context.select_variant('precision-synthetic');p.refresh()
    assert p._rows()==escape_sections(w.context.engine())
    before=identity(w.context.engine());assert p.save_current()
    assert identity(w.context.engine())==before
    path=tmp_path/'precision.json';save_project(path,w.context.project)
    assert escape_sections(load_project(path)['variants']['precision-synthetic'])[0]['length_mm']==83.123456789
    close(w)

def test_history_has_real_viewport_space_at_every_supported_size():
    from PySide6.QtTest import QTest
    w=window()
    for width,height in ((960,630),(1360,900),(1920,1080)):
        w.resize(width,height);APP.processEvents();w._toggle_explorer();QTest.qWait(100)
        assert w.explorer_dock.isFloating()
        assert w.analysis_history.table.viewport().height()>=120
        w.explorer_dock.hide()
    close(w)

def test_engineering_comparison_translates_reason_but_preserves_original_code():
    w=window();w.context.duplicate_variant(None,'B');p=w.results
    rows=[dict(variant_id=name,rpm=3000,classification='MAX_CYCLES_NONCONVERGED',periodicity='INSUFFICIENT_CYCLES',brake_power_status='UNDEFINED',brake_power_reason='NO_PERIODICITY_TRANSIENT_ONLY') for name in ('base','B')]
    p.dataset={'points':rows};p.variants.blockSignals(True);p.variants.clear()
    for name in ('base','B'):
        item=QListWidgetItem(name);item.setCheckState(Qt.CheckState.Checked);p.variants.addItem(item)
    p.variants.blockSignals(False);p._update_engineering_compare()
    cells=[p.compare_table.item(i,4) for i in range(p.compare_table.rowCount())]
    assert any(c.text()=='Sin periodicidad · sólo transitorio' for c in cells)
    assert all('NO_PERIODICITY_TRANSIENT_ONLY' not in c.text() for c in cells)
    assert rows[0]['brake_power_reason']=='NO_PERIODICITY_TRANSIENT_ONLY'
    close(w)
