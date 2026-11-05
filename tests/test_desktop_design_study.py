from __future__ import annotations
import csv,hashlib,json,os
from pathlib import Path
import pytest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QAbstractItemView,QComboBox,QDialog,QFileDialog,QLineEdit,QMessageBox
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.execution_page import ExecutionPage
from motorsim.desktop.results_page import (ResultsPage,_build_cross_study_comparison_csv,
    _build_factorial_effects_csv,_build_parametric_study_export,_factorial_effects_from_study,
    _load_verified_study_comparison,_write_factorial_effects_csv)
from motorsim.desktop.services import load_results,new_design_project
from motorsim.desktop.parametric_factorial_snapshot import import_parametric_factorial_csv_snapshot

APP=QApplication.instance() or QApplication([])


def test_parametric_actions_are_available_and_study_comparison_is_explicit(tmp_path):
    window=DinoDesktopWindow(new_design_project("design-study-ui-test"))
    actions={action.text() for action in window.strip_more.menu().actions()}
    assert "Estudio paramétrico geométrico…" in actions
    assert "Estudio paramétrico por RPM…" in actions
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
             "run_directory":"C:/artifacts/historical-run","historical_source_project_id":"old-project",
             "identity_sha256":"a"*64,"result_sha256":"b"*64,"result_artifact_sha256":"c"*64,
             "factor_values":[{"label":"Transfer top","value":40.12345,"unit":"mm"},
                              {"label":"Cárter","value":355.2,"unit":"cm³"}] }]}
    page.design_study_manifest_path=tmp_path/"study.json"
    page._update_design_study_summary()
    assert not page.design_study_group.isHidden()
    assert page.design_study_table.rowCount()==2
    assert page.design_study_table.item(0,5).text()=="—"
    assert "histórico verificado" in page.design_study_table.item(1,0).text()
    assert "corrida histórica reutilizada" in page.design_study_table.item(1,0).toolTip()
    assert "C:/artifacts/historical-run" in page.design_study_table.item(1,0).toolTip()
    assert "b"*64 in page.design_study_table.item(1,0).toolTip()
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


def test_rpm_envelope_dialog_dispatches_existing_zero_step_preflight(monkeypatch):
    context=DesktopContext(new_design_project("rpm-envelope-dialog"));page=ExecutionPage(context)
    queued={}
    def accept_with_value(dialog):
        dialog.findChild(QLineEdit,"rpmEnvelopeValues").setText("84")
        return QDialog.DialogCode.Accepted
    def record(function,*args,**kwargs):
        queued.update(function=function,args=args,kwargs=kwargs);return object()
    monkeypatch.setattr(QDialog,"exec",accept_with_value)
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",record)
    page.start_design_rpm_envelope()
    assert queued["function"].__name__=="prepare_design_rpm_envelope"
    assert queued["kwargs"]["on_done"]==page._design_study_preflight_done
    assert queued["kwargs"]["rpms"]==[3000,4000]
    assert queued["kwargs"]["values"][0] in queued["kwargs"]["values"]
    assert page.cancel_event is None
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


def test_rpm_envelope_keeps_observed_rpm_rows_and_suppresses_mixed_rpm_response():
    page=ResultsPage(DesktopContext(new_design_project("rpm-envelope-results")))
    def point(run_id,rpm,power):
        return {"run_id":run_id,"variant_id":run_id,"rpm":rpm,
            "classification":"MAX_CYCLES_NONCONVERGED","periodicity":"INSUFFICIENT_CYCLES",
            "cycles_completed":1,"brake_power":None,"brake_power_status":"UNDEFINED",
            "brake_torque":None,"brake_torque_status":"UNDEFINED","BMEP":None,"BMEP_status":"UNDEFINED"}
    page.dataset={"points":[point("base-3000",3000,None),point("base-4000",4000,None),
        point("alt-3000",3000,None),point("alt-4000",4000,None)]}
    page.design_study_manifest={"study_id":"envelope-synthetic","design_method":"RPM_ENVELOPE_V1",
        "rpms":[3000,4000],"parameter":{"label":"Escape length","unit":"mm"},"points":[
            {"run_id":"base-3000","baseline":True,"value":83.0,"unit":"mm","rpm":3000,"status":"COMPLETE"},
            {"run_id":"base-4000","baseline":True,"value":83.0,"unit":"mm","rpm":4000,"status":"COMPLETE"},
            {"run_id":"alt-3000","baseline":False,"value":84.0,"unit":"mm","rpm":3000,"status":"COMPLETE","design_index":1},
            {"run_id":"alt-4000","baseline":False,"value":84.0,"unit":"mm","rpm":4000,"status":"COMPLETE","design_index":1}]}
    page.design_study_manifest_path="synthetic-envelope-study.json"
    page._update_design_study_summary()
    assert page.design_study_table.rowCount()==4
    assert page.design_study_table.item(2,1).text().endswith("3000 RPM")
    assert page.design_study_table.item(2,0).text()=="Diseño 2"
    assert page.design_study_table.item(3,0).text()=="Diseño 2"
    assert "RPM: 3000, 4000" in page.design_study_notice.text()
    assert page.design_response_plot.series==[]
    assert "No se mezclan RPM" in page.design_response_notice.text()
    assert page.design_study_table.item(2,5).text()=="—"
    page.close();APP.processEvents()


def _comparison_fixture(tmp_path,study_id,project_id,baseline,*,rpm=3000,engine_hash=None,
                        identity_hash=None,power=None,periodicity="PERIOD_1",status="COMPLETE",
                        context_overrides=None):
    result_dir=tmp_path/f"{study_id}-run";result_dir.mkdir()
    source_run=f"{study_id}-run"
    identity_hash=identity_hash or hashlib.sha256((study_id+"-identity").encode()).hexdigest()
    result={"schema":"DINO_ENGINEERING_RUN_V1","status":"COMPLETE",
        "classification":"PERIOD_1" if periodicity=="PERIOD_1" else "MAX_CYCLES_NONCONVERGED",
        "periodicity":periodicity,"cycles_completed":3,
        "bindings":{"identity_sha256":identity_hash,"run_id":source_run,"project_id":project_id}}
    result_raw=json.dumps(result,sort_keys=True).encode();result_hash=hashlib.sha256(result_raw).hexdigest()
    (result_dir/"result.json").write_bytes(result_raw)
    (result_dir/"run.json").write_text(json.dumps({"result_sha256":result_hash}),encoding="utf-8")
    engine_hash=engine_hash or hashlib.sha256((study_id+"-engine").encode()).hexdigest()
    context={"fuel_id":"fuel-sha","afr_kg_air_per_kg_fuel":12.5,
        "total_finite_volume_cells":128,"cycles_requested":3,
        "solver_identity_sha256":"solver-sha","implementation_identity_sha256":"implementation-sha"}
    context.update(context_overrides or {})
    point={"index":0,"value":83.0,"unit":"mm","rpm":rpm,"status":status,
        "classification":result["classification"],"periodicity":periodicity,"cycles_completed":3,
        "run_id":source_run,"source_run_id":source_run,"engine_identity_sha256":engine_hash,
        "identity_sha256":identity_hash,"result_sha256":result_hash,"result_artifact_sha256":result_hash,
        "run_directory":str(result_dir)}
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":study_id,
        "project_id":project_id,"baseline_engine_identity_sha256":baseline,"rpm":rpm,
        "parameter":{"id":"exhaust:length","label":"Escape","unit":"mm"},
        "status":"COMPLETE","points":[point]}
    manifest_path=tmp_path/f"{study_id}.study.json"
    raw=json.dumps(manifest,sort_keys=True).encode();manifest_path.write_bytes(raw)
    reference={"path":str(manifest_path),"study_id":study_id,
        "source_project_id":project_id,"schema":manifest["schema"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest()}
    imported={"artifact_directory":str(result_dir),"run_id":source_run,"rpm":rpm,
        "classification":result["classification"],"periodicity":periodicity,
        "cycles_completed":3,**context,
        "brake_power":power,"brake_power_status":"DEFINED" if power is not None else "UNDEFINED",
        "brake_torque":(power or 0)*2 if power is not None else None,
        "brake_torque_status":"DEFINED" if power is not None else "UNDEFINED",
        "BMEP":(power or 0)*10 if power is not None else None,
        "BMEP_status":"DEFINED" if power is not None else "UNDEFINED"}
    return reference,manifest,point,imported,result_dir


def test_cross_study_comparison_verifies_sources_and_pairs_only_exact_periodic_conditions(tmp_path,monkeypatch):
    from motorsim import power_curve
    base="a"*64;project="comparison-source-project"
    ref_a,manifest_a,point_a,row_a,dir_a=_comparison_fixture(tmp_path,"study-a",project,base,power=10.0)
    ref_b,manifest_b,point_b,row_b,dir_b=_comparison_fixture(tmp_path,"study-b",project,base,power=12.0)
    ref_b2,manifest_b2,point_b2,row_b2,dir_b2=_comparison_fixture(
        tmp_path,"study-b2",project,base,rpm=4000,power=None,
        periodicity="INSUFFICIENT_CYCLES",status="COMPLETE")
    ref_b3,manifest_b3,point_b3,row_b3,dir_b3=_comparison_fixture(
        tmp_path,"study-b3",project,base,rpm=3000,power=15.0,
        context_overrides={"total_finite_volume_cells":256})
    mesh_mismatch=dict(manifest_b3["points"][0],index=1)
    different_rpm=dict(manifest_b2["points"][0],index=2)
    manifest_b["points"].extend((mesh_mismatch,different_rpm))
    # Keep both source rows under the same registered study manifest and bind it anew.
    raw=json.dumps(manifest_b,sort_keys=True).encode();Path(ref_b["path"]).write_bytes(raw)
    ref_b={**ref_b,"manifest_sha256":hashlib.sha256(raw).hexdigest()}
    imported_rows={str(path.resolve()).casefold():row for path,row in
        ((dir_a,row_a),(dir_b,row_b),(dir_b2,row_b2),(dir_b3,row_b3))}
    calls=[]
    def importer(paths):
        calls.extend(paths)
        return {"points":[imported_rows[str(Path(path).resolve()).casefold()] for path in paths]}
    monkeypatch.setattr(power_curve,"import_curve_runs",importer)

    comparison=_load_verified_study_comparison([ref_a,ref_b])

    assert comparison["baseline_engine_identity_sha256"]==base
    assert len(comparison["pairs"])==1
    pair=comparison["pairs"][0]
    assert (pair["rpm"],pair["pairing"])==(3000.0,"EXACT_RPM_AND_OPERATING_CONTEXT")
    assert pair["metrics"]["brake_power"]=={"a":10.0,"b":12.0,"delta":2.0}
    assert len(comparison["unpaired"])==2
    transient=next(item["point"] for item in comparison["unpaired"] if item["point"]["rpm"]==4000)
    context_mismatch=next(item["point"] for item in comparison["unpaired"] if item["point"]["rpm"]==3000)
    assert transient["periodicity"]=="INSUFFICIENT_CYCLES"
    assert transient["metrics"]=={"brake_power":None,"brake_torque":None,"BMEP":None}
    assert context_mismatch["context"]["total_finite_volume_cells"]==256
    assert any("RPM exacta" in item["reason"] for item in comparison["unpaired"])
    assert any("total_finite_volume_cells" in item["reason"] for item in comparison["unpaired"])
    assert len(calls)==4


def test_cross_study_comparison_fails_closed_on_baseline_and_source_tampering(tmp_path,monkeypatch):
    from motorsim import power_curve
    project="comparison-integrity-project"
    ref_a,*_,dir_a=_comparison_fixture(tmp_path,"integrity-a",project,"a"*64,power=1.0)
    ref_b,*_,dir_b=_comparison_fixture(tmp_path,"integrity-b",project,"b"*64,power=2.0)
    calls=[];monkeypatch.setattr(power_curve,"import_curve_runs",lambda paths:(calls.append(paths) or {"points":[]}))
    with pytest.raises(ValueError,match="baselines distintos"):
        _load_verified_study_comparison([ref_a,ref_b])
    assert calls==[]

    ref_b,*_,dir_b=_comparison_fixture(tmp_path,"integrity-b2",project,"a"*64,power=2.0)
    (dir_b/"result.json").write_text('{"changed":true}',encoding="utf-8")
    with pytest.raises(ValueError,match="source/hash/identidad"):
        _load_verified_study_comparison([ref_a,ref_b])
    assert calls==[]

    manifest=json.loads(Path(ref_a["path"]).read_text(encoding="utf-8"))
    manifest["points"]=[dict(manifest["points"][0],index=index) for index in range(31)]
    raw=json.dumps(manifest,sort_keys=True).encode()
    oversized=tmp_path/"oversized-study.json";oversized.write_bytes(raw)
    ref_over={**ref_a,"path":str(oversized),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest()}
    with pytest.raises(ValueError,match="30 puntos"):
        _load_verified_study_comparison([ref_a,ref_over])
    assert calls==[]


def test_cross_study_comparison_page_keeps_full_identity_and_metric_states():
    page=ResultsPage(DesktopContext(new_design_project("cross-study-results-page")))
    point_a={"index":0,"value":83.0,"unit":"mm","rpm":3000.0,"status":"COMPLETE",
        "classification":"MAX_CYCLES_NONCONVERGED","periodicity":"INSUFFICIENT_CYCLES",
        "engine_identity_sha256":"a"*64,"identity_sha256":"c"*64,
        "result_sha256":"d"*64,"result_artifact_sha256":"e"*64,"metrics":{"brake_power":None}}
    point_b={**point_a,"engine_identity_sha256":"b"*64,"identity_sha256":"f"*64}
    page._study_comparison_loaded({"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":"9"*64,"studies":[
            {"study_id":"Study-A","manifest_path":"a.study.json","manifest_sha256":"1"*64,"parameter":{"label":"Escape"}},
            {"study_id":"Study-B","manifest_path":"b.study.json","manifest_sha256":"2"*64,"parameter":{"label":"Escape"}}],
        "pairs":[{"study_a":"Study-A","point_a":point_a,"study_b":"Study-B","point_b":point_b,
            "rpm":3000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
            "metrics":{"brake_power":{"a":None,"b":None,"delta":None},
                "brake_torque":{"a":None,"b":None,"delta":None},"BMEP":{"a":None,"b":None,"delta":None}}}],
        "unpaired":[],"notice":"sin interpolación"})
    assert page.study_comparison_table.rowCount()==1
    assert "insuficientes" in page.study_comparison_table.item(0,3).text().lower()
    assert page.study_comparison_table.item(0,4).text()=="—"
    assert "a"*64 in page.study_comparison_table.item(0,2).toolTip()
    assert "RPM exacta:" in page.study_comparison_table.item(0,2).toolTip()
    page.close();APP.processEvents()


def test_cross_study_response_plot_uses_only_exact_period_one_metric_pairs():
    page=ResultsPage(DesktopContext(new_design_project("cross-study-response-plot")))
    studies=[{"study_id":name,"manifest_path":f"{name}.study.json","manifest_sha256":str(index)*64,
        "parameter":{"label":"Escape"}} for index,name in enumerate(("A","B","C"),1)]
    def point(run,rpm,periodicity,power,torque):
        return {"index":rpm,"run_id":run,"rpm":float(rpm),"status":"COMPLETE",
            "classification":periodicity,"periodicity":periodicity,
            "metrics":{"brake_power":power,"brake_torque":torque,"BMEP":None},
            "engine_identity_sha256":"a"*64,"identity_sha256":"b"*64,
            "result_sha256":"c"*64,"result_artifact_sha256":"d"*64}
    a3=point("a-3",3000,"PERIOD_1",10.0,20.0);b3=point("b-3",3000,"PERIOD_1",12.0,24.0)
    b4=point("b-4",4000,"PERIOD_1",16.0,32.0);c4=point("c-4",4000,"PERIOD_1",18.0,36.0)
    a5=point("a-5",5000,"INSUFFICIENT_CYCLES",None,None);c5=point("c-5",5000,"PERIOD_1",22.0,44.0)
    pair=lambda left_id,left,right_id,right,rpm:{"study_a":left_id,"point_a":left,
        "study_b":right_id,"point_b":right,"rpm":float(rpm),
        "pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
        "metrics":{"brake_power":{"a":left["metrics"]["brake_power"],
            "b":right["metrics"]["brake_power"],"delta":None},
            "brake_torque":{"a":left["metrics"]["brake_torque"],
                "b":right["metrics"]["brake_torque"],"delta":None},
            "BMEP":{"a":None,"b":None,"delta":None}}}
    comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":"9"*64,"studies":studies,
        "pairs":[pair("A",a3,"B",b3,3000),pair("B",b4,"C",c4,4000),
                 pair("A",a5,"C",c5,5000)],
        "unpaired":[{"study_id":"A","point":point("a-6",6000,"PERIOD_1",30.0,60.0),
            "reason":"No existe un punto de otro estudio en la misma RPM exacta."}],"notice":"sin interpolación"}

    page._study_comparison_loaded(comparison)

    plotted={series["name"]:series for series in page.study_comparison_response_plot.series}
    assert set(plotted)=={"A","B","C"}
    assert [point["rpm"] for point in plotted["A"]["points"]]==[3000.0]
    assert [point["rpm"] for point in plotted["B"]["points"]]==[3000.0,4000.0]
    assert [point["rpm"] for point in plotted["C"]["points"]]==[4000.0]
    assert all(series["connect"] is False for series in plotted.values())
    assert [point["value"] for point in plotted["B"]["points"]]==[12.0,16.0]
    assert "A · 1 punto(s)" in page.study_comparison_response_legend.text()
    assert "B · 2 punto(s)" in page.study_comparison_response_legend.text()
    assert "1 par(es) exacto(s) excluido(s)" in page.study_comparison_response_notice.text()
    assert page.study_comparison_table.rowCount()==4  # includes the non-periodic pair and unpaired point
    page.study_comparison_metric.setCurrentIndex(page.study_comparison_metric.findData("brake_torque"))
    assert [point["value"] for point in page.study_comparison_response_plot.series[1]["points"]]==[24.0,32.0]
    assert "Torque de freno" in page.study_comparison_response_notice.text()
    page.close();APP.processEvents()


def test_cross_study_response_marker_selects_exact_rows_and_source_traceability():
    page=ResultsPage(DesktopContext(new_design_project("cross-study-marker-inspection")))
    studies=[{"study_id":name,"manifest_path":f"synthetic/{name}.study.json",
        "manifest_sha256":chr(ord("a")+index)*64,"parameter":{"label":"Escape"}}
        for index,name in enumerate(("A","B","C"))]
    def point(index,run,rpm,identity):
        return {"index":index,"run_id":run,"source_run_id":run+"-source","rpm":float(rpm),
            "value":83.123456789,"unit":"mm","status":"COMPLETE","classification":"PERIOD_1",
            "periodicity":"PERIOD_1","cycles_completed":7,"source_verified":True,
            "engine_identity_sha256":identity*64,"identity_sha256":identity.upper()*64,
            "result_sha256":("d" if identity!="b" else "e")*64,
            "result_artifact_sha256":("f" if identity!="b" else "1")*64,
            "run_directory":f"SYNTHETIC/{run}","context":{"afr":12.5},
            "metrics":{"brake_power":{"a":10.25,"b":11.5,"delta":1.25}.get(identity,14.0),
                "brake_torque":None,"BMEP":None}}
    a=point(0,"run-A",3000,"a");b=point(2,"run-B",3000,"b");c=point(1,"run-C",3000,"c")
    def pair(study_a,point_a,study_b,point_b):
        return {"study_a":study_a,"point_a":point_a,"study_b":study_b,"point_b":point_b,
            "rpm":3000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT","metrics":{
                "brake_power":{"a":10.25,"b":11.5,"delta":1.25},
                "brake_torque":{"a":None,"b":None,"delta":None},
                "BMEP":{"a":None,"b":None,"delta":None}}}
    comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":"9"*64,"studies":studies,
        "pairs":[pair("A",a,"B",b),pair("B",b,"C",c)],
        "unpaired":[],"notice":"Fixture de presentación sintético; sin cálculo ni validación."}
    page._study_comparison_loaded(comparison)
    marker=next(p for s in page.study_comparison_response_plot.series if s["name"]=="B" for p in s["points"])
    assert marker["comparison_rows"]==[0,1]
    page.study_comparison_response_plot.pointSelected.emit(marker);APP.processEvents()
    assert "run-B" in page.study_comparison_point_details.toPlainText()
    assert "b"*64 in page.study_comparison_point_details.toPlainText()
    assert "Verificada al cargar" in page.study_comparison_point_details.toPlainText()
    assert "Fila 1: A · run run-A-source" in page.study_comparison_point_details.toPlainText()
    assert "Fila 2: C · run run-C-source" in page.study_comparison_point_details.toPlainText()
    selected=page.study_comparison_table.currentItem()
    assert selected is not None and selected.data(Qt.ItemDataRole.UserRole)==0
    assert page.study_comparison_table.selectionModel().isRowSelected(selected.row(),page.study_comparison_table.rootIndex())
    page.close();APP.processEvents()


def test_parametric_point_details_bind_manifest_nested_sweep_and_source_status(tmp_path):
    from motorsim.desktop.context import DesktopContext
    page=ResultsPage(DesktopContext(new_design_project("study-traceability-details")))
    sweep=tmp_path/"series.json";sweep.write_text('{"schema":"synthetic presentation fixture"}',encoding="utf-8")
    sweep_hash=hashlib.sha256(sweep.read_bytes()).hexdigest()
    points=[{"index":0,"design_index":0,"value":83.0,"unit":"mm","baseline":True,
        "rpm":3000,"status":"COMPLETE","classification":"MAX_CYCLES_NONCONVERGED",
        "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":1,"run_id":"run-3000",
        "source_run_id":"run-3000","engine_identity_sha256":"a"*64,
        "result_artifact_sha256":"b"*64,"run_directory":str(tmp_path/"missing-run"),
        "sweep_manifest":str(sweep),"sweep_manifest_sha256":sweep_hash},
        {"index":1,"design_index":0,"value":83.0,"unit":"mm","baseline":True,
        "rpm":4000,"status":"COMPLETE","classification":"MAX_CYCLES_NONCONVERGED",
        "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":1,"run_id":"run-4000",
        "source_run_id":"run-4000","engine_identity_sha256":"c"*64,
        "result_artifact_sha256":"d"*64,"sweep_manifest":str(sweep),"sweep_manifest_sha256":sweep_hash}]
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"synthetic-rpm-details",
        "project_id":"source-project","design_method":"RPM_ENVELOPE_V1","rpm":3000,
        "rpms":[3000,4000],"parameter":{"id":"exhaust.length","label":"Longitud Escape","unit":"mm"},
        "values":[83.0],"status":"COMPLETE","scientific_validation":"NOT_CLAIMED",
        "groups":[{"index":0,"sweep_manifest":str(sweep),"sweep_manifest_sha256":sweep_hash}],
        "points":points}
    manifest_path=tmp_path/"study.json";raw=json.dumps(manifest,sort_keys=True).encode();manifest_path.write_bytes(raw)

    page.open_design_study(manifest_path)

    first=page.design_study_traceability.toPlainText()
    assert hashlib.sha256(raw).hexdigest() in first
    assert sweep_hash in first
    assert "Verificado: hash coincide" in first
    assert "Fuente no cargada" in first
    assert "NOT_CLAIMED" in first
    page.design_study_table.setCurrentCell(1,0);APP.processEvents()
    assert "Punto 1 · RPM 4000" in page.design_study_traceability.toPlainText()
    assert "run-4000" in page.design_study_traceability.toPlainText()

    sweep.write_text('{"changed":true}',encoding="utf-8")
    page._design_study_point_selected(1)
    assert "FALLÓ: el hash" in page.design_study_traceability.toPlainText()
    manifest_path.write_bytes(raw+b" ")
    page._design_study_point_selected(1)
    assert "CAMBIÓ desde la carga" in page.design_study_traceability.toPlainText()

    old_study_id=page.design_study_manifest.get("study_id")
    page.context.project=new_design_project("different-project")
    page.context.changed.emit();APP.processEvents()
    assert page.design_study_manifest is None
    assert old_study_id not in page.design_study_traceability.toPlainText()
    page.close();APP.processEvents()


def test_factorial_csv_reimport_is_read_only_and_keeps_point_and_contrast_qualification():
    path=Path("results/desktop-parametric-design-study-v2/factor-effects-csv/native-smoke-20261104T200320Z/factorial-export.csv")
    data=load_results(path)
    page=ResultsPage(DesktopContext(new_design_project("factorial-csv-snapshot-view")))

    page._show_parametric_factorial_csv_snapshot(data,path)

    assert not page.factorial_csv_snapshot_group.isHidden()
    assert page.result_tabs.currentIndex()==3
    assert page.factorial_csv_snapshot_points.rowCount()==4
    assert page.factorial_csv_snapshot_contrasts.rowCount()==9
    assert page.factorial_csv_snapshot_points.item(0,1).text()=="0.0 mm"
    assert page.factorial_csv_snapshot_points.item(0,8).text()=="10.0"
    assert page.factorial_csv_snapshot_points.item(0,11).text()=="Verificada ahora"
    assert page.factorial_csv_snapshot_contrasts.item(0,3).text()=="Descriptivo disponible · no validado"
    assert "El CSV de origen omitió" in page.factorial_csv_snapshot_notice.text()
    assert "4 verificado ahora (hash e identidad)" in page.factorial_csv_snapshot_notice.text()
    assert "CURRENT_HASH_AND_IDENTITY_MATCH" not in page.factorial_csv_snapshot_notice.text()
    assert "NOT_CLAIMED" in page.factorial_csv_snapshot_notice.text()
    assert page.plot.series==[]
    assert page.design_study_table.rowCount()==0
    assert page.export_table_button.isHidden()
    assert page.factorial_csv_snapshot_detail.toPlainText().find("result_artifact_sha256")>=0
    page.factorial_csv_snapshot_points.setCurrentCell(1,0);APP.processEvents()
    assert "factorial-source-1" in page.factorial_csv_snapshot_detail.toPlainText()
    page.factorial_csv_snapshot_contrasts.setCurrentCell(0,0);APP.processEvents()
    missing_binding=page.factorial_csv_snapshot_detail.toPlainText()
    assert '"contrast_source_binding_status": "NOT_PRESENT_IN_EXPORTED_CONTRAST_ROW"' in missing_binding
    assert "no registró bindings para este contraste; no se reconstruyen" in missing_binding
    assert json.loads(missing_binding)["contrast_source_run_ids"]==[None,None,None,None]
    page.close();APP.processEvents()


def test_cross_study_csv_export_keeps_exact_sources_pair_decisions_and_blank_nonperiodic_metrics(tmp_path,monkeypatch):
    base="9"*64
    point_a={"index":0,"value":38.40862784470379,"unit":"mm","rpm":3000.0,
        "status":"COMPLETE","classification":"PERIOD_1","periodicity":"PERIOD_1","cycles_completed":5,
        "run_id":"run-a","source_run_id":"run-a-source","engine_identity_sha256":"a"*64,
        "identity_sha256":"b"*64,"result_sha256":"c"*64,"result_artifact_sha256":"d"*64,
        "run_directory":"C:/synthetic/a","source_manifest_point":{"index":0,"value":38.40862784470379,
            "unit":"mm","factor_values":[{"id":"transfer_top","value":40.123456789,"unit":"mm"}]}}
    point_b={"index":2,"value":41.98765432109876,"unit":"mm","rpm":3000.0,
        "status":"COMPLETE","classification":"PERIOD_1","periodicity":"PERIOD_1","cycles_completed":5,
        "run_id":"run-b","source_run_id":"run-b-source","engine_identity_sha256":"e"*64,
        "identity_sha256":"f"*64,"result_sha256":"1"*64,"result_artifact_sha256":"2"*64,
        "run_directory":"C:/synthetic/b","source_manifest_point":{"index":2,"value":41.98765432109876,
            "unit":"mm","factor_values":[]}}
    point_transient={"index":3,"value":44.1234567890123,"unit":"mm","rpm":4000.0,
        "status":"COMPLETE","classification":"MAX_CYCLES_NONCONVERGED","periodicity":"INSUFFICIENT_CYCLES",
        "cycles_completed":2,"run_id":"run-b-transient","source_run_id":"run-b-transient",
        "engine_identity_sha256":"3"*64,"identity_sha256":"4"*64,"result_sha256":"5"*64,
        "result_artifact_sha256":"6"*64,"run_directory":"C:/synthetic/b-transient",
        "source_manifest_point":{"index":3,"value":44.1234567890123,"unit":"mm"}}
    study_files=[]
    for study_id in ("study-a","study-b"):
        manifest_path=tmp_path/f"{study_id}.study.json"
        manifest_raw=json.dumps({"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":study_id,
            "project_id":"synthetic-project","baseline_engine_identity_sha256":base,"points":[]},
            sort_keys=True,separators=(",",":")).encode()
        manifest_path.write_bytes(manifest_raw)
        study_files.append({"study_id":study_id,"manifest_path":str(manifest_path),
            "manifest_sha256":hashlib.sha256(manifest_raw).hexdigest(),"parameter":{"label":"Escape"}})
    verified_dir=tmp_path/"verified-run-a";verified_dir.mkdir()
    verified_result={"schema":"DINO_ENGINEERING_RUN_V1","status":"COMPLETE",
        "bindings":{"run_id":"run-a-source","identity_sha256":point_a["identity_sha256"]}}
    verified_raw=json.dumps(verified_result,sort_keys=True,separators=(",",":")).encode()
    verified_hash=hashlib.sha256(verified_raw).hexdigest()
    (verified_dir/"result.json").write_bytes(verified_raw)
    (verified_dir/"run.json").write_text(json.dumps({"result_sha256":verified_hash}),encoding="utf-8")
    point_a.update({"run_directory":str(verified_dir),"result_sha256":verified_hash,
        "result_artifact_sha256":verified_hash,"source_verified":True})
    study_files[0]["points"]=[point_a]
    study_files[1]["points"]=[point_b,point_transient]
    comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":base,"scientific_validation":"NOT_CLAIMED",
        "notice":"sin interpolación ni reclamos predictivos.",
        "studies":study_files,
        "pairs":[{"study_a":"study-a","point_a":point_a,"study_b":"study-b","point_b":point_b,
            "rpm":3000.0,"pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
            "metrics":{"brake_power":{"a":12.3456789012345,"b":13.4567890123456,"delta":1.1111101111111},
                "brake_torque":{"a":4.1,"b":4.5,"delta":0.4},"BMEP":{"a":130.1,"b":131.2,"delta":1.1}}}],
        "unpaired":[{"study_id":"study-b","point":point_transient,
            "reason":"No existe una corrida compatible a 4000 RPM."}]}
    rows=_build_cross_study_comparison_csv(comparison)
    assert len(rows)==2
    pair,unpaired=rows
    assert pair["row_type"]=="EXACT_PAIR"
    assert pair["point_a_design_value"]==38.40862784470379
    assert json.loads(pair["point_a_factor_values_json"])[0]["value"]==40.123456789
    assert pair["study_a_manifest_sha256"]==study_files[0]["manifest_sha256"]
    assert pair["study_b_manifest_sha256"]==study_files[1]["manifest_sha256"]
    assert pair["point_a_source_verified"] is True
    assert pair["point_a_source_run_id"]=="run-a-source"
    assert pair["brake_power_delta_kw"]==1.1111101111111
    assert unpaired["row_type"]=="UNPAIRED" and unpaired["pairing_reason"]=="No existe una corrida compatible a 4000 RPM."
    assert unpaired["point_b_periodicity"]=="INSUFFICIENT_CYCLES"
    assert unpaired["brake_power_a_kw"]==unpaired["brake_power_b_kw"]==unpaired["brake_power_delta_kw"]==""

    page=ResultsPage(DesktopContext(new_design_project("cross-study-csv-native-handler")))
    assert not page.export_study_comparison_csv_button.isEnabled()
    page._study_comparison_loaded(comparison)
    assert page.export_study_comparison_csv_button.isEnabled()
    destination=tmp_path/"comparison.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(destination),"CSV (*.csv)"))
    assert page.export_study_comparison_csv() is True
    with destination.open(encoding="utf-8-sig",newline="") as stream:
        records=list(csv.DictReader(stream))
    assert len(records)==2 and records[0]["pairing_status"]=="EXACT_RPM_AND_OPERATING_CONTEXT"
    assert records[1]["point_b_design_value"]=="44.1234567890123"
    assert records[1]["point_b_classification"]=="MAX_CYCLES_NONCONVERGED"
    assert "SHA-256" in page.study_comparison_notice.text()
    monkeypatch.setattr(QMessageBox,"warning",lambda *args:None)
    assert page.export_study_comparison_csv() is False
    assert len(list(csv.DictReader(destination.open(encoding="utf-8-sig",newline=""))))==2
    (verified_dir/"result.json").write_text("{}",encoding="utf-8")
    stale_artifact=tmp_path/"stale-artifact.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(stale_artifact),"CSV (*.csv)"))
    assert page.export_study_comparison_csv() is False
    assert not stale_artifact.exists()
    tampered=Path(study_files[1]["manifest_path"]);tampered.write_text("{}",encoding="utf-8")
    new_destination=tmp_path/"stale-comparison.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(new_destination),"CSV (*.csv)"))
    assert page.export_study_comparison_csv() is False
    assert not new_destination.exists()
    page.context.project["study_references"]=[{"path":item["manifest_path"],"study_id":item["study_id"],
        "manifest_sha256":item["manifest_sha256"]} for item in study_files]
    page.context.changed.emit();APP.processEvents()
    assert page.study_comparison is None
    assert not page.export_study_comparison_csv_button.isEnabled()
    page.close();APP.processEvents()


def _factorial_effect_fixture(tmp_path):
    axes=[{"parameter":{"id":"A","label":"Factor A","unit":"mm"},"values":[0.0,1.0]},
        {"parameter":{"id":"B","label":"Factor B","unit":"cm3"},"values":[10.0,20.0]}]
    context={"fuel_id":"fuel","afr_kg_air_per_kg_fuel":12.5,"total_finite_volume_cells":128,
        "cycles_requested":5,"solver_identity_sha256":"solver","implementation_identity_sha256":"impl"}
    samples=[(0.0,10.0,10.0),(0.0,20.0,14.0),(1.0,10.0,20.0),(1.0,20.0,28.0)]
    points=[];imported=[]
    for index,(a,b,power) in enumerate(samples):
        run_id=f"factorial-source-{index}";identity=hashlib.sha256(f"identity-{index}".encode()).hexdigest()
        result_dir=tmp_path/f"factorial-run-{index}";result_dir.mkdir()
        result={"schema":"DINO_ENGINEERING_RUN_V1","status":"COMPLETE",
            "bindings":{"run_id":run_id,"identity_sha256":identity}}
        raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode();digest=hashlib.sha256(raw).hexdigest()
        (result_dir/"result.json").write_bytes(raw)
        (result_dir/"run.json").write_text(json.dumps({"result_sha256":digest}),encoding="utf-8")
        points.append({"index":index,"status":"COMPLETE","run_id":run_id,"source_run_id":run_id,
            "rpm":3000,"periodicity":"PERIOD_1","classification":"PERIOD_1","cycles_completed":5,
            "factor_values":[{"parameter_id":"A","value":a},{"parameter_id":"B","value":b}],
            "identity_sha256":identity,"engine_identity_sha256":identity,"result_sha256":digest,
            "result_artifact_sha256":digest,"run_directory":str(result_dir)})
        imported.append({"artifact_directory":str(result_dir),"run_id":run_id,"rpm":3000,
            "result_sha256":digest,"identity_sha256":identity,"periodicity":"PERIOD_1",
            "classification":"PERIOD_1","cycles_completed":5,**context,
            "brake_power":power,"brake_power_status":"DEFINED",
            "brake_torque":power*2,"brake_torque_status":"DEFINED",
            "BMEP":power*3,"BMEP_status":"DEFINED"})
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","design_method":"FACTORIAL_2X2_V1",
        "study_id":"factorial-effect-synthetic","project_id":"synthetic-factorial","rpm":3000,
        "baseline_engine_identity_sha256":"b"*64,"factors":axes,
        "parameter":{"id":"factorial-2x2","label":"2×2 · Factor A × Factor B","axes":[a["parameter"] for a in axes]},
        "points":points,"scientific_validation":"NOT_CLAIMED"}
    return manifest,imported


def test_factorial_contrasts_require_four_verified_periodic_exact_context_points(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    effects=_factorial_effects_from_study(manifest,imported)
    assert effects["status"]=="AVAILABLE"
    power={row["term"]:row["value"] for row in effects["metrics"][0]["effects"]}
    assert power["Efecto principal · Factor A"]==12.0
    assert power["Efecto principal · Factor B"]==6.0
    assert power["Interacción A×B"]==4.0
    assert all(row["status"]=="DEFINED" for row in effects["metrics"])
    assert all(len(point["run_id"])>0 for point in manifest["points"])

    transient=[dict(row) for row in imported];transient[-1]["periodicity"]="INSUFFICIENT_CYCLES"
    unavailable=_factorial_effects_from_study(manifest,transient)
    assert unavailable["status"]=="UNAVAILABLE"
    assert "no periódico" in unavailable["reason"].lower()
    assert all(effect["value"] is None for metric in unavailable["metrics"] for effect in metric["effects"])
    missing_point=_factorial_effects_from_study({**manifest,"points":manifest["points"][:-1]},imported[:-1])
    assert missing_point["status"]=="UNAVAILABLE" and "cuatro" in missing_point["reason"].lower()

    (Path(manifest["points"][0]["run_directory"])/"result.json").write_text("{}",encoding="utf-8")
    stale=_factorial_effects_from_study(manifest,imported)
    assert stale["status"]=="UNAVAILABLE" and "hash" in stale["reason"].lower()


def test_factorial_ui_keeps_four_rows_and_shows_unavailable_effects_for_transient_points(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    imported[-1]["periodicity"]="INSUFFICIENT_CYCLES"
    imported[-1]["classification"]="MAX_CYCLES_NONCONVERGED"
    manifest["points"][-1]["periodicity"]="INSUFFICIENT_CYCLES"
    manifest["points"][-1]["classification"]="MAX_CYCLES_NONCONVERGED"
    page=ResultsPage(DesktopContext(new_design_project("factorial-effect-ui-synthetic")))
    page.design_study_manifest=manifest;page.design_study_manifest_path=tmp_path/"manifest.json"
    page.dataset={"points":imported}
    page._update_design_study_summary()
    assert page.design_study_table.rowCount()==4
    assert "Factor A=0" in page.design_study_table.item(0,1).text()
    assert "Factor B=10" in page.design_study_table.item(0,1).text()
    assert "None=" not in page.design_study_table.item(0,1).text()
    assert not page.factor_effects_group.isHidden()
    assert page.factor_effects_table.rowCount()==9
    assert all(metric["status"]=="UNAVAILABLE" for metric in page.factor_effects_plot.metrics)
    assert all(effect["value"] is None for metric in page.factor_effects_plot.metrics for effect in metric["effects"])
    assert all(page.factor_effects_table.item(index,2).text()=="—" for index in range(9))
    assert "no periódico" in page.factor_effects_notice.text().lower()
    page.close();APP.processEvents()


def test_factorial_effect_plot_uses_verified_signed_values_and_renders(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    for point,value in zip(imported,[30.0,40.0,10.0,25.0]):
        point["BMEP"]=value
    page=ResultsPage(DesktopContext(new_design_project("factorial-effect-plot-synthetic")))
    page.design_study_manifest=manifest;page.design_study_manifest_path=tmp_path/"manifest.json"
    page.dataset={"points":imported};page._update_design_study_summary();APP.processEvents()
    assert len(page.factor_effects_plot.metrics)==3
    assert all(metric["status"]=="DEFINED" for metric in page.factor_effects_plot.metrics)
    assert [effect["value"] for effect in page.factor_effects_plot.metrics[0]["effects"]]==[12.0,6.0,4.0]
    assert [effect["value"] for effect in page.factor_effects_plot.metrics[0]["effects"]][0]>0
    assert [effect["value"] for effect in page.factor_effects_plot.metrics[2]["effects"]]==[-17.5,12.5,5.0]
    assert page.factor_effects_plot.metrics[2]["effects"][0]["value"]<0
    assert "Escala independiente" in page.factor_effects_plot.toolTip()
    page.factor_effects_plot.resize(900,276)
    assert not page.factor_effects_plot.grab().isNull()
    page.close();APP.processEvents()


def test_factorial_effect_plot_export_binds_png_csv_and_manifest_hash(tmp_path,monkeypatch):
    from PySide6.QtGui import QImageReader
    context=DesktopContext(new_design_project("synthetic-factorial"))
    manifest,imported=_factorial_effect_fixture(tmp_path)
    manifest_path=tmp_path/"factorial-source.study.json"
    raw=json.dumps(manifest,sort_keys=True).encode("utf-8");manifest_path.write_bytes(raw)
    reference={"path":str(manifest_path),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":manifest["project_id"]}
    context.add_study_reference(reference)
    page=ResultsPage(context);page.design_study_manifest=manifest
    page.design_study_manifest_path=manifest_path;page.design_study_manifest_sha256=reference["manifest_sha256"]
    page.dataset={"points":imported};page._update_design_study_summary();APP.processEvents()
    output=tmp_path/"factorial-effect.png";warnings=[]
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a:(str(output),"PNG (*.png)"))
    monkeypatch.setattr(QMessageBox,"warning",lambda *a:warnings.append(a[2]))
    assert page.export_factorial_plot_button.isEnabled()
    assert page.export_factorial_effect_plot() is True
    csv_path=tmp_path/"factorial-effect.factorial-effects.csv"
    receipt_path=tmp_path/"factorial-effect.factorial-effects.json"
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    csv_bytes=csv_path.read_bytes();png_bytes=output.read_bytes()
    assert hashlib.sha256(csv_bytes).hexdigest()==receipt["csv_sha256"]
    assert hashlib.sha256(png_bytes).hexdigest()==receipt["plot_sha256"]
    assert receipt["manifest_sha256"]==reference["manifest_sha256"]
    assert receipt["scientific_validation"]=="NOT_CLAIMED"
    with csv_path.open(encoding="utf-8-sig",newline="") as stream:
        exported=list(csv.DictReader(stream))
    assert len(exported)==13
    assert sum(row["record_type"]=="CONTRAST" for row in exported)==9
    reader=QImageReader(str(output));rendered=reader.read();assert not rendered.isNull()
    assert rendered.text("Dino.study_id")==manifest["study_id"]
    assert rendered.text("Dino.factorial_csv_sha256")==receipt["csv_sha256"]
    assert "NOT_CLAIMED" in rendered.text("Dino.scientific_qualification")
    assert page.export_factorial_effect_plot() is False
    assert output.read_bytes()==png_bytes and csv_path.read_bytes()==csv_bytes
    assert warnings and "no se sobrescriben" in warnings[-1]
    stale_output=tmp_path/"stale.png"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a:(str(stale_output),"PNG (*.png)"))
    page.dataset["points"][0]["brake_power"]+=1.0
    assert page.export_factorial_effect_plot() is False
    assert not stale_output.exists()
    assert "figura visible no coincide" in warnings[-1]
    tampered_output=tmp_path/"tampered.png"
    manifest_path.write_text(json.dumps(dict(manifest,rpm=3100),sort_keys=True),encoding="utf-8")
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a:(str(tampered_output),"PNG (*.png)"))
    assert page.export_factorial_effect_plot() is False
    assert not tampered_output.exists()
    assert not (tmp_path/"tampered.factorial-effects.csv").exists()
    assert not (tmp_path/"tampered.factorial-effects.json").exists()
    assert "manifiesto cambió" in warnings[-1]
    page.close();APP.processEvents()


def test_factorial_effects_flow_into_desktop_technical_report(tmp_path,monkeypatch):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    manifest_path=tmp_path/"verified-factorial.study.json"
    manifest_path.write_text(json.dumps(manifest,sort_keys=True),encoding="utf-8")
    page=ResultsPage(DesktopContext(new_design_project("factorial-report-export-synthetic")))
    page.dataset={"schema":"DINO_EXPLORATORY_COMPARISON_V1","experimental_validation":"NOT_PERFORMED",
        "points":[{**row,"variant_id":"synthetic factorial"} for row in imported]}
    page.source_kind="EXPLORATORY";page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
    page.variants.addItem("synthetic factorial");page.variants.item(0).setCheckState(Qt.CheckState.Checked)
    output=tmp_path/"factorial-report.html"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(output),"HTML (*.html)"))
    assert page.export_technical_report() is True
    report=output.read_text(encoding="utf-8")
    assert "Efecto principal · Factor A" in report and "+12 kW" in report and "+4 kW" in report
    assert "Contrastes factoriales 2×2 · descriptivos" in report
    page.close();APP.processEvents()


def test_factorial_csv_binds_four_exact_points_and_nine_qualified_contrasts(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    imported[0]["brake_power"]=10.123456789012345
    manifest_path=tmp_path/"factorial.study.json"
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
    rows=_build_factorial_effects_csv(manifest_path,digest,manifest,imported)
    points=[row for row in rows if row["record_type"]=="POINT"]
    contrasts=[row for row in rows if row["record_type"]=="CONTRAST"]
    assert len(points)==4 and len(contrasts)==9
    assert all(row["source_verified"] is True and row["manifest_sha256"]==digest for row in points)
    assert points[0]["factor_a_label"]=="Factor A" and points[0]["factor_b_value"]==10.0
    assert points[0]["brake_power_kw"]==10.123456789012345
    assert all(row["scientific_validation"]=="NOT_CLAIMED" for row in rows)
    assert {row["contrast_term"] for row in contrasts}=={
        "Efecto principal · Factor A","Efecto principal · Factor B","Interacción A×B"}
    expected_source_ids=[row["source_run_id"] for row in points]
    expected_source_hashes=[row["result_sha256"] for row in points]
    assert all(json.loads(row["contrast_source_run_ids_json"])==expected_source_ids for row in contrasts)
    assert all(json.loads(row["contrast_source_result_sha256s_json"])==expected_source_hashes
        for row in contrasts)
    output=tmp_path/"factorial.csv"
    _write_factorial_effects_csv(output,rows)
    with output.open(encoding="utf-8-sig",newline="") as stream:
        reopened=list(csv.DictReader(stream))
    assert len(reopened)==13
    assert reopened[0]["brake_power_kw"]==repr(imported[0]["brake_power"])
    assert reopened[-1]["contrast_source_result_sha256s_json"]
    original=output.read_bytes()
    with pytest.raises(FileExistsError):_write_factorial_effects_csv(output,rows)
    assert output.read_bytes()==original
    manifest_path.write_text("{}",encoding="utf-8")
    with pytest.raises(ValueError,match="manifiesto factorial cambió"):
        _build_factorial_effects_csv(manifest_path,digest,manifest,imported)


def test_factorial_contrast_source_bindings_survive_read_only_csv_reimport(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    manifest_path=tmp_path/"factorial-roundtrip.study.json"
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
    rows=_build_factorial_effects_csv(manifest_path,digest,manifest,imported)
    csv_path=tmp_path/"factorial-roundtrip.csv"
    _write_factorial_effects_csv(csv_path,rows)
    snapshot=import_parametric_factorial_csv_snapshot(csv_path)
    assert snapshot["snapshot"]["contrast_source_bindings"]=="MATCH_POINT_ROWS"
    points=snapshot["snapshot_points"]
    point_ids=[row["source_run_id"] for row in points]
    point_hashes=[row["result_sha256"] for row in points]
    contrasts=snapshot["snapshot_contrasts"]
    assert len(points)==4 and len(contrasts)==9
    assert all(row["contrast_source_binding_status"]=="MATCHES_POINT_ROWS" for row in contrasts)
    assert all(json.loads(row["contrast_source_run_ids_json"])==point_ids for row in contrasts)
    assert all(json.loads(row["contrast_source_result_sha256s_json"])==point_hashes
        for row in contrasts)
    assert snapshot["snapshot"]["read_only"] is True
    assert snapshot["experimental_validation"]=="NOT_CLAIMED"
    page=ResultsPage(DesktopContext(new_design_project("factorial-source-binding-reimport-view")))
    page._show_parametric_factorial_csv_snapshot(snapshot,csv_path)
    assert page.factorial_csv_snapshot_points.rowCount()==4
    assert page.factorial_csv_snapshot_contrasts.rowCount()==9
    assert "Las filas CONTRAST enlazan las cuatro fuentes POINT" in page.factorial_csv_snapshot_notice.text()
    assert "NOT_CLAIMED" in page.factorial_csv_snapshot_notice.text()
    source_detail=page._factorial_contrast_traceability_detail(contrasts[0])
    page.factorial_csv_snapshot_contrasts.setCurrentCell(0,0);APP.processEvents()
    selected_detail=page.factorial_csv_snapshot_detail.toPlainText()
    assert page.factorial_csv_snapshot_contrasts.selectionBehavior()==QAbstractItemView.SelectionBehavior.SelectRows
    assert all(run_id in selected_detail for run_id in point_ids)
    assert all(digest in selected_detail for digest in point_hashes)
    assert "MATCHES_POINT_ROWS" in selected_detail and "coinciden con las filas POINT" in selected_detail
    assert source_detail==page.factorial_csv_snapshot_contrasts.item(0,0).data(Qt.ItemDataRole.UserRole)
    assert json.loads(selected_detail)["contrast_source_run_ids"]==point_ids
    assert json.loads(selected_detail)["contrast_source_result_sha256s"]==point_hashes
    page.close();APP.processEvents()


def test_parametric_study_summary_shows_manifest_budget_and_interruption_without_runtime_estimate():
    page=ResultsPage(DesktopContext(new_design_project("study-lifecycle-summary")))
    page.design_study_manifest={
        "schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"synthetic-cancelled-study",
        "design_method":"FACTORIAL_2X2_V1","parameter":{"label":"Factor A × Factor B"},
        "rpm":3000,"status":"CANCELLED","stop_reason":"CANCELLED",
        "total_budget_seconds":240.0,"elapsed_seconds":75.5,
        "scientific_validation":"NOT_CLAIMED","points":[
            {"index":0,"value":0.0,"unit":"mm","baseline":True,"status":"COMPLETE",
             "periodicity":"PERIOD_1","classification":"PERIOD_1","cycles_completed":5},
            {"index":1,"value":1.0,"unit":"mm","status":"MAX_CYCLES_NONCONVERGED",
             "periodicity":"INSUFFICIENT_CYCLES","classification":"MAX_CYCLES_NONCONVERGED",
             "cycles_completed":5},
            {"index":2,"value":2.0,"unit":"mm","status":"NOT_STARTED"},
        ]}
    page.design_study_manifest_path=None
    page.dataset={"points":[]}
    page._update_design_study_summary()
    summary=page.design_study_lifecycle_notice.text()
    assert "Presupuesto asignado: 240 s" in summary
    assert "tiempo consumido registrado: 75.5 s" in summary
    assert "Estado: Cancelado · puntos completos: 1/3 · incompletos/no iniciados: 2 · motivo: cancelación solicitada" in summary
    assert "No se estima el tiempo restante" in summary
    assert "validación científica NO RECLAMADA" in page.design_study_notice.text()

    page.design_study_manifest={"study_id":"legacy-no-budget","status":"PREPARED",
        "parameter":{"label":"Legacy parameter"},"rpm":3000,"points":[]}
    page._update_design_study_summary()
    summary=page.design_study_lifecycle_notice.text()
    assert "Presupuesto asignado: no registrado" in summary
    assert "tiempo consumido: no registrado" in summary
    assert "0 s" not in summary
    page.close();APP.processEvents()


def test_factorial_csv_keeps_nonperiodic_points_and_withholds_all_contrasts(tmp_path):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    imported[-1]["periodicity"]="INSUFFICIENT_CYCLES"
    imported[-1]["classification"]="MAX_CYCLES_NONCONVERGED"
    manifest["points"][-1]["periodicity"]="INSUFFICIENT_CYCLES"
    manifest["points"][-1]["classification"]="MAX_CYCLES_NONCONVERGED"
    manifest_path=tmp_path/"factorial-nonperiodic.study.json"
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
    rows=_build_factorial_effects_csv(manifest_path,digest,manifest,imported)
    points=[row for row in rows if row["record_type"]=="POINT"]
    contrasts=[row for row in rows if row["record_type"]=="CONTRAST"]
    assert len(points)==4 and len(contrasts)==9
    assert points[-1]["classification"]=="MAX_CYCLES_NONCONVERGED"
    assert points[-1]["brake_power_kw"]==""
    assert points[-1]["brake_power_qualification"]=="WITHHELD_NONPERIODIC"
    assert all(row["contrast_value"]=="" and row["contrast_status"]=="UNAVAILABLE" for row in contrasts)
    assert all("no periódico" in row["contrast_reason"].lower() for row in contrasts)


def test_factorial_csv_export_button_uses_project_bound_manifest_and_no_overwrite(tmp_path,monkeypatch):
    manifest,imported=_factorial_effect_fixture(tmp_path)
    manifest_path=tmp_path/"factorial-ui.study.json"
    raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
    context=DesktopContext(new_design_project("factorial-csv-export-synthetic"))
    context.project["study_references"]=[{"path":str(manifest_path),"study_id":manifest["study_id"],
        "manifest_sha256":digest}]
    page=ResultsPage(context);page.dataset={"points":imported}
    page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
    page._update_design_study_summary()
    assert not page.export_factorial_effects_button.isHidden()
    assert page.export_factorial_effects_button.isEnabled()
    output=tmp_path/"factorial-button.csv";warnings=[]
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(output),"CSV (*.csv)"))
    monkeypatch.setattr(QMessageBox,"warning",lambda *args:warnings.append(args[2]))
    page.export_factorial_effects_button.click()
    assert output.is_file() and "4 puntos y 9 contrastes exportados" in page.design_study_notice.text()
    original=output.read_bytes();page.export_factorial_effects_button.click()
    assert output.read_bytes()==original and warnings
    manifest_path.write_text("{}",encoding="utf-8")
    tampered=tmp_path/"factorial-tampered.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(tampered),"CSV (*.csv)"))
    assert page.export_factorial_effects_csv() is False and not tampered.exists()
    page.close();APP.processEvents()


def test_cross_study_comparison_control_requires_multiple_project_references():
    context=DesktopContext(new_design_project("cross-study-selection-state"))
    page=ResultsPage(context)
    assert not page.compare_studies_button.isEnabled()
    references=[{"path":f"{name}.study.json","study_id":name,"manifest_sha256":digest,
        "schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","source_project_id":context.project["project_id"]}
        for name,digest in (("Study A","a"*64),("Study B","b"*64))]
    context.project["study_references"]=references;context.changed.emit();APP.processEvents()
    assert page.compare_studies_button.isEnabled()
    assert not page.study_comparison_group.isHidden()
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


def test_completed_study_manifest_is_registered_and_reopens_from_project(tmp_path):
    from motorsim.engine_project import load_project,save_project
    from motorsim.desktop.services import new_design_project
    context=DesktopContext(new_design_project("study-project-reference"));execution=ExecutionPage(context)
    manifest_path=tmp_path/"study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"study-roundtrip",
        "project_id":context.project["project_id"],"rpm":3000,
        "parameter":{"label":"Synthetic factor","unit":"mm"},"points":[]}
    manifest_path.write_text(json.dumps(manifest,sort_keys=True),encoding="utf-8")
    emitted=[];execution.design_study_completed.connect(emitted.append)
    execution._done({"schema":"DINO_PARAMETRIC_DESIGN_STUDY_RESULT_V1","status":"COMPLETE",
        "study_id":"study-roundtrip","bindings":{"project_id":context.project["project_id"]},
        "points":[],"design_study_manifest":str(manifest_path)})
    reference=context.project["study_references"][0]
    assert reference["study_id"]=="study-roundtrip"
    assert reference["source_project_id"]==context.project["project_id"]
    assert reference["manifest_sha256"]==hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert emitted==[reference]
    project_path=tmp_path/"project.dino2t.json";save_project(project_path,context.project)
    reopened=load_project(project_path)
    assert reopened["study_references"]==context.project["study_references"]
    duplicate=__import__("motorsim.engine_project",fromlist=["duplicate_project"]).duplicate_project(
        reopened,project_id="study-project-copy")
    assert duplicate["study_references"]==reopened["study_references"]

    page=ResultsPage(DesktopContext(reopened));page.show()
    assert page.project_study_selector.count()==1
    assert page.open_selected_project_study() is True
    assert page.design_study_manifest["study_id"]=="study-roundtrip"
    assert not page.design_study_group.isHidden()
    page.close();execution.close();APP.processEvents()


def test_project_study_reference_rejects_changed_manifest(tmp_path):
    from motorsim.desktop.services import new_design_project
    context=DesktopContext(new_design_project("tampered-study-project"))
    path=tmp_path/"study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"tamper-study",
        "project_id":context.project["project_id"],"rpm":3000,"parameter":{"label":"test"},"points":[]}
    raw=json.dumps(manifest,sort_keys=True).encode("utf-8");path.write_bytes(raw)
    context.add_study_reference({"path":str(path),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":manifest["project_id"]})
    page=ResultsPage(context);path.write_text(json.dumps(dict(manifest,study_id="changed")),encoding="utf-8")
    assert page.open_selected_project_study() is False
    assert "SHA-256 no coincide" in page.design_study_notice.text()
    assert getattr(page,"design_study_manifest",None) is None
    page.close();APP.processEvents()


def test_selected_project_study_routes_to_existing_resume_flow(monkeypatch,tmp_path):
    window=DinoDesktopWindow(new_design_project("resume-study-from-results"))
    manifest_path=tmp_path/"study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"resume-study",
        "project_id":window.context.project["project_id"],"rpm":3000,
        "parameter":{"label":"Synthetic factor"},"points":[]}
    raw=json.dumps(manifest,sort_keys=True).encode("utf-8");manifest_path.write_bytes(raw)
    reference={"path":str(manifest_path),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":manifest["project_id"]}
    window.context.add_study_reference(reference);APP.processEvents()
    calls=[]
    monkeypatch.setattr(window.pages[3],"resume_design_study",lambda selected=None:calls.append(selected))
    monkeypatch.setattr(window.pages[3],"refresh",lambda *_:None)
    assert window.results.project_study_selector.count()==1
    window.results.project_study_selector.setCurrentIndex(0)
    window.results.resume_project_study_button.click();APP.processEvents()
    assert window.mode_stack.currentIndex()==2
    assert calls==[reference]
    window.context.dirty=False
    window.close();APP.processEvents()


def test_resume_from_project_reference_rejects_changed_manifest_before_worker(monkeypatch,tmp_path):
    context=DesktopContext(new_design_project("resume-study-tamper"))
    path=tmp_path/"study.json"
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"resume-study-tamper",
        "project_id":context.project["project_id"],"rpm":3000,
        "parameter":{"label":"Synthetic factor"},"points":[]}
    raw=json.dumps(manifest,sort_keys=True).encode("utf-8");path.write_bytes(raw)
    reference={"path":str(path),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":manifest["project_id"]}
    context.add_study_reference(reference)
    path.write_text(json.dumps(dict(manifest,rpm=4000),sort_keys=True),encoding="utf-8")
    page=ExecutionPage(context);warnings=[];workers=[]
    monkeypatch.setattr(QMessageBox,"warning",lambda *args:warnings.append(args[2]))
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",lambda *a,**k:workers.append((a,k)))
    page.resume_design_study(reference)
    assert warnings and "SHA-256 no coincide" in warnings[0]
    assert workers==[] and page.task is None
    page.close();APP.processEvents()


def test_resume_from_selected_project_study_reuses_existing_preflight(monkeypatch,tmp_path):
    from motorsim.engine_configuration import identity
    import motorsim.design_study as design_study
    context=DesktopContext(new_design_project("resume-study-valid-reference"))
    project_id=context.project["project_id"]
    artifact_root=tmp_path/"artifacts"
    manifest_path=artifact_root/"design-studies-v1"/project_id/"resume-study-valid"/"study.json"
    manifest_path.parent.mkdir(parents=True)
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"resume-study-valid",
        "project_id":project_id,"rpm":3000,"parameter":{"label":"Synthetic factor"},"points":[]}
    raw=json.dumps(manifest,sort_keys=True).encode("utf-8");manifest_path.write_bytes(raw)
    reference={"path":str(manifest_path),"study_id":manifest["study_id"],
        "manifest_sha256":hashlib.sha256(raw).hexdigest(),"schema":manifest["schema"],
        "source_project_id":project_id}
    context.add_study_reference(reference)
    page=ExecutionPage(context);loaded=[];workers=[]
    prepared={"project_id":project_id,"variant_label":"base",
        "baseline_engine_identity_sha256":identity(context.engine()),"artifact_root":str(artifact_root),
        "study_id":manifest["study_id"],"points":[],"rpm":3000,"max_cycles":2,
        "total_budget_seconds":60}
    monkeypatch.setattr(design_study,"load_prepared_study",lambda path:(loaded.append(path) or prepared))
    monkeypatch.setattr("motorsim.desktop.execution_page.QInputDialog.getInt",lambda *a,**k:(0,True))
    monkeypatch.setattr("motorsim.desktop.execution_page.QMessageBox.question",
        lambda *a,**k:QMessageBox.StandardButton.Yes)
    monkeypatch.setattr("motorsim.desktop.preferences.set_artifact_root",lambda path:None)
    monkeypatch.setattr("motorsim.desktop.execution_page.run_background",
        lambda function,*args,**kwargs:(workers.append((function,args,kwargs)) or object()))
    page.resume_design_study(reference)
    assert loaded==[manifest_path.resolve()]
    assert len(workers)==1 and workers[0][0] is design_study.run_design_study
    assert workers[0][2]["resume"] is True
    assert workers[0][2]["additional_budget_seconds"]==0
    assert page.status_text=="REANUDANDO ESTUDIO"
    page.close();APP.processEvents()


def test_parametric_study_csv_export_preserves_precision_states_and_verified_sources(tmp_path,monkeypatch):
    context=DesktopContext(new_design_project("study-csv-export-synthetic"))
    source_dir=tmp_path/"run-periodic";source_dir.mkdir()
    identity=hashlib.sha256(b"synthetic-engine-identity").hexdigest()
    run_id="synthetic-periodic-run"
    result={"schema":"DINO_ENGINEERING_RUN_V1","classification":"PERIOD_1",
        "periodicity":"PERIOD_1","cycles_completed":4,
        "bindings":{"run_id":run_id,"identity_sha256":identity,
                    "project_id":context.project["project_id"]}}
    result_raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result_hash=hashlib.sha256(result_raw).hexdigest()
    (source_dir/"result.json").write_bytes(result_raw)
    (source_dir/"run.json").write_text(json.dumps({"result_sha256":result_hash}),encoding="utf-8")
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"synthetic-export-study",
        "project_id":context.project["project_id"],"design_method":"GEOMETRY_V1","rpm":3000,
        "baseline_engine_identity_sha256":"b"*64,"scientific_validation":"NOT_CLAIMED",
        "parameter":{"id":"exhaust:length","label":"Longitud del escape","unit":"mm"},
        "points":[
            {"index":0,"value":38.40862784470379,"unit":"mm","rpm":3000,"status":"COMPLETE",
             "run_id":run_id,"source_run_id":run_id,"engine_identity_sha256":"e"*64,
             "identity_sha256":identity,"result_sha256":result_hash,"result_artifact_sha256":result_hash,
             "run_directory":str(source_dir),"classification":"PERIOD_1","periodicity":"PERIOD_1",
             "cycles_completed":4,"factor_values":[{"id":"transfer_top","value":40.123456789,"unit":"mm"}]},
            {"index":1,"value":41.98765432109876,"unit":"mm","rpm":3000,"status":"COMPLETE",
             "run_id":"synthetic-nonconverged-run","source_run_id":"synthetic-nonconverged-run",
             "engine_identity_sha256":"f"*64,"identity_sha256":"a"*64,"result_sha256":"d"*64,
             "run_directory":str(tmp_path/"missing-nonconverged"),"classification":"MAX_CYCLES_NONCONVERGED",
             "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":2,
             "factor_values":[{"id":"transfer_top","value":41.234567891,"unit":"mm"}]}]}
    manifest_path=tmp_path/"synthetic.study.json"
    manifest_raw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
    manifest_path.write_bytes(manifest_raw)
    digest=hashlib.sha256(manifest_raw).hexdigest()
    context.add_study_reference({"path":str(manifest_path),"study_id":manifest["study_id"],
        "source_project_id":context.project["project_id"],"schema":manifest["schema"],
        "manifest_sha256":digest})
    page=ResultsPage(context)
    page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
    page.dataset={"points":[{"artifact_directory":str(source_dir),"run_id":run_id,"rpm":3000,
        "result_sha256":result_hash,
        "classification":"PERIOD_1","periodicity":"PERIOD_1","cycles_completed":4,
        "brake_power":12.3456789012345,"brake_power_status":"DEFINED",
        "brake_torque":7.6543210987654,"brake_torque_status":"DEFINED",
        "BMEP":123.456789012345,"BMEP_status":"DEFINED"}]}
    page._update_design_study_summary()
    assert page.design_study_table.rowCount()==2
    assert page.design_study_table.item(0,2).text()=="Periódica · ciclo 1"
    assert page.design_study_table.item(0,3).text()=="Periódica · ciclo 1"
    assert "no convergida" in page.design_study_table.item(1,2).text().lower()
    assert "insuficientes" in page.design_study_table.item(1,3).text().lower()
    from PySide6.QtCore import QItemSelectionModel
    selection=page.design_study_table.selectionModel()
    selection.select(page.design_study_table.model().index(0,0),
        QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows)
    selection.select(page.design_study_table.model().index(1,0),
        QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows)
    output=tmp_path/"selected-points.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(output),"CSV (*.csv)"))
    assert page.export_design_study_csv() is True
    with output.open(encoding="utf-8-sig",newline="") as stream:
        records=list(csv.DictReader(stream))
    assert len(records)==2
    first,second=records
    assert float(first["design_value"])==38.40862784470379
    assert json.loads(first["factor_values_json"])[0]["value"]==40.123456789
    assert first["source_verification"]=="VERIFIED_HASH_AND_IDENTITY",first
    assert first["manifest_sha256"]==digest and first["source_verified"]=="True",first
    assert first["source_verification"]=="VERIFIED_HASH_AND_IDENTITY"
    assert first["brake_power_kw"]=="12.3456789012345"
    assert first["scientific_validation"]=="NOT_CLAIMED"
    assert second["classification"]=="MAX_CYCLES_NONCONVERGED"
    assert second["periodicity"]=="INSUFFICIENT_CYCLES"
    assert second["source_verified"]=="False"
    assert second["brake_power_kw"]==""
    assert (source_dir/"result.json").read_bytes()==result_raw
    assert "SHA-256 del manifiesto" in page.design_study_notice.text()
    assert _build_parametric_study_export(manifest,manifest_path,digest,[0],page.dataset["points"])[0]["source_verified"]
    page.close();APP.processEvents()


def test_parametric_study_csv_export_rejects_manifest_tampering_and_existing_target(tmp_path,monkeypatch):
    context=DesktopContext(new_design_project("study-csv-export-integrity"))
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"integrity-export",
        "project_id":context.project["project_id"],"rpm":3000,
        "parameter":{"id":"exhaust:length","label":"Escape","unit":"mm"},
        "points":[{"index":0,"value":38.4,"unit":"mm","status":"COMPLETE"}]}
    manifest_path=tmp_path/"study.json";manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    raw=manifest_path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    context.add_study_reference({"path":str(manifest_path),"study_id":manifest["study_id"],
        "source_project_id":context.project["project_id"],"schema":manifest["schema"],"manifest_sha256":digest})
    page=ResultsPage(context);page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
    page._update_design_study_summary();page.design_study_table.selectRow(0)
    output=tmp_path/"existing.csv";output.write_text("keep",encoding="utf-8")
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(output),"CSV (*.csv)"))
    monkeypatch.setattr(QMessageBox,"warning",lambda *args:None)
    assert page.export_design_study_csv() is False
    assert output.read_text(encoding="utf-8")=="keep"
    manifest_path.write_text(json.dumps(dict(manifest,study_id="tampered")),encoding="utf-8")
    fresh=tmp_path/"new.csv"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args:(str(fresh),"CSV (*.csv)"))
    assert page.export_design_study_csv() is False
    assert not fresh.exists()
    page.close();APP.processEvents()


def test_recompleted_study_replaces_its_stale_project_reference(tmp_path):
    context=DesktopContext(__import__("motorsim.desktop.services",fromlist=["new_design_project"]).new_design_project("study-reference-refresh"))
    first={"path":str(tmp_path/"first.json"),"study_id":"same-study","manifest_sha256":"a"*64,
        "schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","source_project_id":context.project["project_id"]}
    second={**first,"path":str(tmp_path/"resumed.json"),"manifest_sha256":"b"*64}
    assert context.add_study_reference(first) is True
    assert context.add_study_reference(second) is True
    assert context.project["study_references"]==[second]
