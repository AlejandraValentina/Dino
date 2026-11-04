from __future__ import annotations
import hashlib,json,os
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication,QComboBox,QDialog,QLineEdit,QMessageBox
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
    assert "Estudio factorial de diseño 2×2…" in actions
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
             "status":"CACHED","baseline":False,"value":182.,"unit":"mm","cycles_completed":1,
             "factor_values":[{"label":"Transfer top","value":40.12345,"unit":"mm"},
                              {"label":"Cárter","value":355.2,"unit":"cm³"}] }]}
    page.design_study_manifest_path=tmp_path/"study.json"
    page._update_design_study_summary()
    assert not page.design_study_group.isHidden()
    assert page.design_study_table.rowCount()==2
    assert page.design_study_table.item(0,5).text()=="—"
    assert "histórico verificado" in page.design_study_table.item(1,0).text()
    assert "Corrida histórica reutilizada" in page.design_study_table.item(1,0).toolTip()
    assert "Transfer top=40.123" in page.design_study_table.item(1,1).text()
    assert "Cárter=355.2 cm³" in page.design_study_table.item(1,1).text()
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


def test_factorial_dialog_preflights_four_combinations_in_background(monkeypatch):
    context=DesktopContext(new_design_project("design-study-factorial-dialog"));page=ExecutionPage(context)
    queued={}
    def accept_factorial(dialog):
        from motorsim.design_study import available_parameters
        parameters=available_parameters(context.engine())
        first=dialog.findChild(QComboBox,"factorialParameter0")
        second=dialog.findChild(QComboBox,"factorialParameter1")
        second.setCurrentIndex(1)
        dialog.findChild(QLineEdit,"factorialAlternative0").setText(str(parameters[0]["baseline"]+1))
        dialog.findChild(QLineEdit,"factorialAlternative1").setText(str(parameters[1]["baseline"]+1))
        return QDialog.DialogCode.Accepted
    def record(function,*args,**kwargs):queued.update(function=function,args=args,kwargs=kwargs);return object()
    monkeypatch.setattr(QDialog,"exec",accept_factorial)
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",record)
    page.start_factorial_design_study()
    assert queued["function"].__name__=="prepare_factorial_design_study"
    assert len(queued["kwargs"]["factors"])==2
    assert queued["kwargs"]["total_budget_seconds"]>=4*queued["kwargs"]["point_budget_seconds"]
    assert page.status_text.startswith("VALIDANDO FACTORIAL")
    page.task=None;page.close();APP.processEvents()


def test_project_historical_references_are_forwarded_to_study_runner(tmp_path,monkeypatch):
    context=DesktopContext(new_design_project("design-study-reference-forward-test"))
    reference={"path":str(tmp_path/"historical"/"result.json"),
        "identity_sha256":"a"*64,"artifact_sha256":"b"*64,"classification":"PERIOD_1"}
    context.project["result_references"]=[reference]
    page=ExecutionPage(context);page.artifact_root=tmp_path;queued={}
    prepared={"project_id":context.project["project_id"],"variant_label":"base",
        "parameter":{"unit":"mm","label":"synthetic parameter"},"values":[1.,2.],
        "rpm":3000.,"max_cycles":1,"total_budget_seconds":60.,"study_id":"reference-test",
        "points":[{},{}]}
    monkeypatch.setattr("motorsim.storage_preflight.check_storage_requirements",lambda *args,**kwargs:None)
    monkeypatch.setattr(QMessageBox,"question",lambda *args,**kwargs:QMessageBox.StandardButton.Yes)
    def record(function,*args,**kwargs):queued.update(function=function,args=args,kwargs=kwargs);return object()
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",record)
    page._design_study_preflight_done(prepared)
    assert queued["function"].__name__=="run_design_study"
    assert queued["kwargs"]["history_references"]==[reference]
    page.task=None;page.close();APP.processEvents()


def test_parametric_response_plots_only_defined_periodic_markers():
    context=DesktopContext(new_design_project("design-study-response-view-test"));page=ResultsPage(context)
    def point(run_id,value,periodicity,classification,power):
        return {"run_id":run_id,"variant_id":run_id,"rpm":3000,
            "classification":classification,"periodicity":periodicity,"cycles_completed":1,
            "brake_power":power,"brake_power_status":"DEFINED" if power is not None else "UNDEFINED",
            "brake_torque":power*2 if power is not None else None,
            "brake_torque_status":"DEFINED" if power is not None else "UNDEFINED",
            "BMEP":power*3 if power is not None else None,
            "BMEP_status":"DEFINED" if power is not None else "UNDEFINED"}
    page.dataset={"points":[point("base",80,"PERIOD_1","PERIOD_1",8.0),
        point("alt",82,"PERIOD_1","PERIOD_1",9.0),
        point("transient",84,"INSUFFICIENT_CYCLES","MAX_CYCLES_NONCONVERGED",None)]}
    page.design_study_manifest={"study_id":"response-synthetic","rpm":3000,
        "parameter":{"label":"Escape cone length","unit":"mm"},"points":[
            {"run_id":"base","baseline":True,"value":80.0,"unit":"mm","status":"COMPLETE"},
            {"run_id":"alt","baseline":False,"value":82.0,"unit":"mm","status":"COMPLETE"},
            {"run_id":"transient","baseline":False,"value":84.0,"unit":"mm","status":"COMPLETE"}]}
    page._update_design_study_summary()
    assert page.design_response_plot.series[0]["points"][0]["value"]==8.0
    assert page.design_response_plot.series[0]["connect"] is False
    assert [row["value"] for row in page.design_response_plot.series[1]["points"]]==[9.0,None]
    assert "2 punto(s) periódico(s)" in page.design_response_notice.text()
    assert page.design_study_table.item(2,2).text()!="PERIOD_1"
    page.design_response_metric.setCurrentIndex(1)
    assert page.design_response_plot.series[0]["points"][0]["value"]==16.0
    page.close();APP.processEvents()


def test_factorial_study_is_not_collapsed_into_one_dimensional_response():
    page=ResultsPage(DesktopContext(new_design_project("factorial-response-view-test")))
    page.dataset={"points":[]}
    page.design_study_manifest={"study_id":"factorial-response-test","rpm":3000,
        "parameter":{"label":"factor A × factor B","axes":[{"id":"a"},{"id":"b"}]},"points":[]}
    page._update_design_study_summary()
    assert page.design_response_plot.series==[]
    assert "No se reduce una matriz factorial" in page.design_response_notice.text()
    page.close();APP.processEvents()


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
