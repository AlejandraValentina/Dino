from __future__ import annotations
import hashlib,json,os
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication,QComboBox,QDialog,QLineEdit
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.execution_page import ExecutionPage
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project

APP=QApplication.instance() or QApplication([])


def test_parametric_actions_are_available_and_study_comparison_is_explicit(tmp_path):
    window=DinoDesktopWindow(new_design_project("design-study-ui-test"))
    actions={action.text() for action in window.strip_more.menu().actions()}
    assert "Estudio paramétrico geométrico…" in actions
    assert "Reanudar estudio paramétrico…" in actions
    context=DesktopContext(window.context.project);page=ResultsPage(context)
    baseline={"run_id":"run-base","variant_id":"study · baseline","brake_power":None,
        "brake_power_status":"UNDEFINED","brake_torque":None,"brake_torque_status":"UNDEFINED",
        "BMEP":None,"BMEP_status":"UNDEFINED","classification":"MAX_CYCLES_NONCONVERGED",
        "periodicity":"NOT_EVALUATED","cycles_completed":1}
    candidate={"run_id":"run-var","variant_id":"study · variant","brake_power":None,
        "brake_power_status":"UNDEFINED","brake_torque":None,"brake_torque_status":"UNDEFINED",
        "BMEP":None,"BMEP_status":"UNDEFINED","classification":"MAX_CYCLES_NONCONVERGED",
        "periodicity":"NOT_EVALUATED","cycles_completed":1}
    historical=dict(candidate,run_id="historical-run",variant_id="old study label")
    page.dataset={"points":[baseline,historical]}
    page.design_study_manifest={"study_id":"synthetic-study","rpm":3000,
        "parameter":{"label":"Escape · diffuser · longitud"},"points":[
            {"run_id":"run-base","baseline":True,"value":180.,"unit":"mm","status":"COMPLETE","cycles_completed":1},
            {"run_id":"run-var","source_run_id":"historical-run","reused_verified":True,
             "status":"CACHED","baseline":False,"value":182.,"unit":"mm","cycles_completed":1}]}
    page.design_study_manifest_path=tmp_path/"study.json"
    page._update_design_study_summary()
    assert not page.design_study_group.isHidden()
    assert page.design_study_table.rowCount()==2
    assert page.design_study_table.item(0,5).text()=="—"
    assert "histórico verificado" in page.design_study_table.item(1,0).text()
    assert "Corrida histórica reutilizada" in page.design_study_table.item(1,0).toolTip()
    assert "NO RECLAMADA" in page.design_study_notice.text()
    window.close();page.close();APP.processEvents()


def test_parametric_preflight_runs_in_background_not_the_ui_thread(monkeypatch):
    context=DesktopContext(new_design_project("design-study-async-test"));page=ExecutionPage(context)
    queued={}
    def accept_with_value(dialog):
        dialog.findChild(QLineEdit,"designStudyValues").setText("85")
        return QDialog.DialogCode.Accepted
    def record(function,*args,**kwargs):
        queued.update(function=function,args=args,kwargs=kwargs)
        return object()
    monkeypatch.setattr(QDialog,"exec",accept_with_value)
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",record)
    page.start_design_study()
    assert queued["function"].__name__=="prepare_design_study"
    assert queued["kwargs"]["on_done"]==page._design_study_preflight_done
    assert page.cancel_event is None
    assert "VALIDANDO" in page.status_text
    page.task=None;page.close();APP.processEvents()


def test_parametric_dialog_uses_selected_axis_units(monkeypatch):
    context=DesktopContext(new_design_project("design-study-units-test"));page=ExecutionPage(context)
    queued={}
    def accept_with_crankcase(dialog):
        parameter=dialog.findChild(QComboBox,"designStudyParameter")
        index=parameter.findData("crankcase.volume_bdc_cm3");parameter.setCurrentIndex(index)
        values=dialog.findChild(QLineEdit,"designStudyValues")
        assert "cm³" in values.placeholderText()
        values.setText("366")
        return QDialog.DialogCode.Accepted
    def record(function,*args,**kwargs):
        queued.update(function=function,args=args,kwargs=kwargs);return object()
    monkeypatch.setattr(QDialog,"exec",accept_with_crankcase)
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",record)
    page.start_design_study()
    assert queued["kwargs"]["parameter_id"]=="crankcase.volume_bdc_cm3"
    assert queued["kwargs"]["values"]==[context.engine()["native_configuration"]["slider_crank"]["crankcase"]["volume_bdc_cm3"],366.0]
    page.task=None;page.close();APP.processEvents()


def test_completed_study_adds_schema_valid_result_references(tmp_path):
    from motorsim.engine_project import validate_project
    context=DesktopContext(new_design_project("design-study-result-ref-test"));page=ExecutionPage(context)
    run_dir=tmp_path/"run";run_dir.mkdir();result_path=run_dir/"result.json";result_path.write_bytes(b'{"synthetic":true}\n')
    digest=hashlib.sha256(result_path.read_bytes()).hexdigest()
    point_identity="a"*64
    page._done({"schema":"DINO_PARAMETRIC_DESIGN_STUDY_RESULT_V1","status":"COMPLETE",
        "classification":"EXPLORATORY_PARAMETRIC_STUDY","curve_availability":"EXPLORATORY_CURVE_PARTIAL",
        "bindings":{"project_id":context.project["project_id"]},"design_study_manifest":None,
        "points":[{"status":"COMPLETE","run_directory":str(run_dir),"result_artifact_sha256":digest,
            "identity_sha256":point_identity,"classification":"MAX_CYCLES_NONCONVERGED"}]})
    validate_project(context.project)
    assert context.project["result_references"]==[{"path":str(result_path),"identity_sha256":point_identity,
        "artifact_sha256":digest,"classification":"MAX_CYCLES_NONCONVERGED"}]
    page.close();APP.processEvents()
