from __future__ import annotations
import hashlib,json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from motorsim.desktop.preferences import artifact_root
from motorsim.desktop.services import new_design_project
from motorsim.design_study import available_parameters,prepare_design_rpm_envelope,run_design_rpm_envelope
from motorsim.power_curve import import_curve_runs

project=new_design_project("synthetic-rpm-envelope-smoke-20261104")
engine=project["base_engine"]
parameter=available_parameters(engine)[0]
root=artifact_root()
prepared=prepare_design_rpm_envelope(engine,parameter_id=parameter["id"],
    values=[parameter["baseline"],parameter["baseline"]+5.0],rpms=[3000,4000],
    max_cycles=1,point_budget_seconds=45,total_budget_seconds=180,memory_limit_mib=512,
    project_id=project["project_id"],variant_label="synthetic-test",artifact_root=root,
    study_id="synthetic-rpm-envelope-smoke-20261104")
result=run_design_rpm_envelope(prepared)
manifest_path=Path(result["design_study_manifest"])
raw=manifest_path.read_bytes();manifest=json.loads(raw)
run_dirs=sorted({point["run_directory"] for point in manifest["points"] if point.get("run_directory")})
imported=import_curve_runs(run_dirs) if run_dirs else {"points":[]}
summary={"schema":"DINO_PARAMETRIC_RPM_ENVELOPE_SMOKE_V1","project_id":project["project_id"],
    "study_id":result["study_id"],"status":result["status"],"design_method":manifest.get("design_method"),
    "rpm_grid":manifest.get("rpms"),"design_values":manifest.get("values"),
    "combination_count":len(manifest.get("points",[])),"elapsed_seconds":manifest.get("elapsed_seconds"),
    "manifest_path":str(manifest_path),"manifest_sha256":hashlib.sha256(raw).hexdigest(),
    "imported_point_count":len(imported.get("points",[])),
    "point_states":[{"rpm":point.get("rpm"),"value":point.get("value"),"status":point.get("status"),
        "classification":point.get("classification"),"periodicity":point.get("periodicity"),
        "run_directory":point.get("run_directory")} for point in manifest.get("points",[])],
    "synthetic_configuration":engine.get("provenance",{}),"predictive_claim":"NOT_CLAIMED"}
print(json.dumps(summary,indent=2,ensure_ascii=False))
if result["status"]!="COMPLETE" or len(manifest.get("points",[]))!=4 or len(imported.get("points",[]))!=4:
    raise SystemExit("integration smoke acceptance failed")
