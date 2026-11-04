from __future__ import annotations

import json
import math
import os
import threading
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from motorsim.design_study import (available_parameters, load_prepared_study,
    prepare_design_study, run_design_study)
from motorsim.engine_configuration import identity,validate
from motorsim.desktop.services import new_design_project


@pytest.fixture
def starter():
    return new_design_project("synthetic-design-study-test")


def prepared(starter, *, study_id="test-design-study"):
    engine=starter["base_engine"]
    parameter=available_parameters(engine)[0]
    return prepare_design_study(engine,parameter_id=parameter["id"],
        values=[parameter["baseline"],parameter["baseline"]+2.0],rpm=3000,
        max_cycles=1,point_budget_seconds=30,total_budget_seconds=60,
        memory_limit_mib=512,project_id=starter["project_id"],variant_label="base",study_id=study_id)


def test_preparation_keeps_baseline_and_creates_distinct_valid_solver_identities(starter):
    engine=starter["base_engine"];before=identity(engine)
    plan=prepared(starter)
    assert identity(engine)==before
    assert len(plan["points"])==2
    assert all(point["preflight"]["solver_steps"]==0 for point in plan["points"])
    assert plan["points"][0]["baseline"] is True
    assert plan["points"][0]["engine_identity_sha256"]!=plan["points"][1]["engine_identity_sha256"]
    assert plan["scientific_validation"]=="NOT_CLAIMED"


def test_preparation_requires_baseline_unique_values_and_preserved_topology(starter):
    engine=starter["base_engine"];parameter=available_parameters(engine)[0]
    with pytest.raises(ValueError,match="baseline"):
        prepare_design_study(engine,parameter_id=parameter["id"],values=[81.,82.],rpm=3000,
            max_cycles=1,point_budget_seconds=20,total_budget_seconds=40,project_id=starter["project_id"])
    with pytest.raises(ValueError,match="únicos"):
        prepare_design_study(engine,parameter_id=parameter["id"],values=[80.,80.],rpm=3000,
            max_cycles=1,point_budget_seconds=20,total_budget_seconds=40,project_id=starter["project_id"])


def test_preparation_rejects_missing_engineering_displacement_without_inference(starter):
    import copy
    engine=copy.deepcopy(starter["base_engine"])
    parameter=available_parameters(engine)[0]
    engine["native_configuration"]["geometry_identity"].pop("displacement_cc")
    from motorsim.engine_configuration import sha256
    engine["native_configuration_sha256"]=sha256(engine["native_configuration"])
    with pytest.raises(ValueError,match="displacement_cc explícito"):
        prepare_design_study(engine,parameter_id=parameter["id"],
            values=[parameter["baseline"],parameter["baseline"]+1],rpm=3000,
            max_cycles=1,point_budget_seconds=20,total_budget_seconds=40,
            project_id=starter["project_id"])


def test_port_dimension_adapter_rebuilds_solver_event_and_area_profiles(starter):
    engine=starter["base_engine"]
    parameter=next(p for p in available_parameters(engine)
        if p["id"]=="port:primary-window:top_mm")
    plan=prepare_design_study(engine,parameter_id=parameter["id"],
        values=[parameter["baseline"],parameter["baseline"]+1.0],rpm=3000,
        max_cycles=1,point_budget_seconds=20,total_budget_seconds=40,
        project_id=starter["project_id"])
    base,changed=(validate(point["engine_document"]) for point in plan["points"])
    port_a=next(port for port in base.port_binding.port_set.ports if port.id==parameter["port_id"])
    port_b=next(port for port in changed.port_binding.port_set.ports if port.id==parameter["port_id"])
    assert base.port_binding.port_set.event_angles(port_a) != changed.port_binding.port_set.event_angles(port_b)
    assert base.port_binding.port_set.area_at(port_a,180) != changed.port_binding.port_set.area_at(port_b,180)
    after_geometry=plan["points"][1]["engine_document"]["native_configuration"]["geometry_identity"]
    transfer_openings=[]
    for port in changed.port_binding.port_set.ports:
        if port.role!="transfer":continue
        for event in changed.port_binding.port_set.event_angles(port):
            if changed.port_binding.port_set.area_at(port,(event+1e-4)%360)>1e-9 and \
                    changed.port_binding.port_set.area_at(port,(event-1e-4)%360)<=1e-9:
                transfer_openings.append(event)
    assert after_geometry["transfer_opens_atdc_deg"]==pytest.approx(min(transfer_openings))
    assert after_geometry["transfer_effective_width_mm"]==pytest.approx(
        sum(port.width_mm for port in changed.port_binding.port_set.ports if port.role=="transfer"))
    for point in plan["points"]:
        native=point["engine_document"]["native_configuration"]
        assert native["geometry_identity"]["ports"]==native["port_binding"]["port_set"]
        assert point["engine_document"]["provenance"]["parametric_study"]["classification"]=="SYNTHETIC_ASSUMPTION"


def test_crankcase_volume_adapter_updates_solver_geometry_and_initial_species(starter):
    engine=starter["base_engine"]
    parameter=next(p for p in available_parameters(engine)
        if p["id"]=="crankcase.volume_bdc_cm3")
    plan=prepare_design_study(engine,parameter_id=parameter["id"],
        values=[parameter["baseline"],parameter["baseline"]+10.0],rpm=3000,
        max_cycles=1,point_budget_seconds=20,total_budget_seconds=40,
        project_id=starter["project_id"])
    base,changed=(point["engine_document"] for point in plan["points"])
    base_solver,changed_solver=(validate(document) for document in (base,changed))
    base_volume=base_solver._geometry(0.0,3000).crankcase_volume_m3
    changed_volume=changed_solver._geometry(0.0,3000).crankcase_volume_m3
    assert changed_volume-base_volume==pytest.approx(10e-6)
    for name in ("crankcase","cylinder"):
        before=base["native_configuration"]["initial_chambers"]["species"][name]
        after=changed["native_configuration"]["initial_chambers"]["species"][name]
        assert [mass/math.fsum(before) for mass in before]==pytest.approx(
            [mass/math.fsum(after) for mass in after])
    geometry=changed["native_configuration"]["geometry_identity"]
    assert geometry["crankcase_volume_bdc_cc"]==pytest.approx(parameter["baseline"]+10)
    assert geometry["crankcase_compression_ratio"]==pytest.approx(changed_solver.slider_crank.crankcase.compression_ratio)


def test_study_interrupt_persists_manifest_and_resume_uses_same_run_checkpoint(monkeypatch,tmp_path,starter):
    plan=prepared(starter);cancel=threading.Event();calls=[]
    def fake_run(document,*,project_id,run_id,artifact_root,resume,**kwargs):
        run_dir=Path(artifact_root)/"exploratory-workflow-v1"/project_id/run_id
        run_dir.mkdir(parents=True,exist_ok=True)
        calls.append((run_id,resume))
        if len(calls)==1:
            cancel.set();status="INTERRUPTED_CHECKPOINTED"
            elapsed=4.0
        else:
            status="COMPLETE";elapsed=7.0 if run_id.endswith("p00") else 3.0
        payload={"status":status,"bindings":{"identity_sha256":identity(document)},"test_only":True}
        (run_dir/"result.json").write_text(json.dumps(payload),encoding="utf-8")
        return {"status":status,"classification":"EXPLORATORY_COMPLETE_PERIODICITY_NOT_IDENTIFIED",
            "periodicity":"NOT_EVALUATED","cycles_completed":1 if resume else 0,
            "artifact_directory":str(run_dir),"bindings":{"identity_sha256":identity(document)},
            "result_sha256":"0"*64,"elapsed_seconds":elapsed}
    monkeypatch.setattr("motorsim.engineering_workflow.run",fake_run)
    first=run_design_study(plan,artifact_root=tmp_path,cancel_event=cancel)
    assert first["status"]=="CANCELLED"
    manifest_path=Path(first["design_study_manifest"])
    saved=json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["points"][0]["status"]=="INTERRUPTED_CHECKPOINTED"
    assert saved["points"][1]["status"]=="NOT_STARTED"
    loaded=load_prepared_study(manifest_path)
    cancel.clear()
    final=run_design_study(loaded,artifact_root=tmp_path,cancel_event=cancel,resume=True,additional_budget_seconds=10)
    assert final["status"]=="COMPLETE"
    assert all(point.get("identity_sha256") for point in final["points"])
    assert calls[0][0]==calls[1][0] and calls[0][1] is False and calls[1][1] is True
    assert calls[-1][0]==saved["points"][1]["run_id"]
    assert final["points"][0]["elapsed_seconds"]==7.0
    assert final["points"][1]["elapsed_seconds"]==3.0


def test_saved_prepared_configuration_hash_detects_tampering(tmp_path,starter):
    plan=prepared(starter)
    result=run_design_study(plan,artifact_root=tmp_path,cancel_event=threading.Event())
    manifest=Path(result["design_study_manifest"])
    prepared_file=manifest.parent/"prepared.json"
    data=json.loads(prepared_file.read_text(encoding="utf-8"));data["points"][0]["engine_document"]["display_name"]="altered"
    prepared_file.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):
        load_prepared_study(manifest)


def test_complete_points_are_reused_only_after_artifact_import_verification(monkeypatch,tmp_path,starter):
    plan=prepared(starter,study_id="verified-reuse-study");calls=[]
    expected={point["engine_identity_sha256"]:point["preflight"]["identity_sha256"]
        for point in plan["points"]}
    def fake_run(document,*,project_id,run_id,artifact_root,**kwargs):
        calls.append(run_id);run_dir=Path(artifact_root)/"exploratory-workflow-v1"/project_id/run_id
        run_dir.mkdir(parents=True,exist_ok=True)
        payload={"status":"COMPLETE","bindings":{"identity_sha256":expected[identity(document)]},"classification":"MAX_CYCLES_NONCONVERGED",
            "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":1,"result_sha256":"1"*64}
        (run_dir/"result.json").write_text(json.dumps(payload),encoding="utf-8")
        (run_dir/"run.json").write_text(json.dumps({"stub":True}),encoding="utf-8")
        return {"status":"COMPLETE","bindings":payload["bindings"],"classification":payload["classification"],
            "periodicity":payload["periodicity"],"cycles_completed":1,"artifact_directory":str(run_dir),
            "result_sha256":payload["result_sha256"],"elapsed_seconds":1.0}
    monkeypatch.setattr("motorsim.engineering_workflow.run",fake_run)
    first=run_design_study(plan,artifact_root=tmp_path)
    assert len(calls)==2
    monkeypatch.setattr("motorsim.engineering_workflow.import_desktop_runs",
        lambda paths:{"points":[{"point_configuration_sha256":"a"*64}]})
    second=run_design_study(load_prepared_study(first["design_study_manifest"]),artifact_root=tmp_path,resume=True)
    assert len(calls)==2
    assert all(point.get("reused_verified") is True for point in second["points"])
    assert all(point.get("identity_sha256") for point in second["points"])
