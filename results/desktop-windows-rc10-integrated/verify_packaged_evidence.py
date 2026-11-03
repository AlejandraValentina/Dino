"""Read-only verification of artifacts produced through the rc10 Windows GUI.

No solver calls, campaigns, geometry edits, or artifact rewrites.
Run from the repository root with --artifact-root pointing at Desktop artifacts.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from motorsim.desktop.services import load_results
from motorsim.engine_configuration import resolve_for_operating_point, sha256


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()
    out = Path(__file__).parent
    project = read(out / "synthetic-case.dino2t.json")
    package = read(out / "package.json")
    base = project["base_engine"]["native_configuration"]
    variant = project["variants"]["escape-plus20"]["native_configuration"]
    assert base["slider_crank"]["crankcase"]["bore_mm"] == 57
    assert base["slider_crank"]["crankcase"]["volume_bdc_cm3"] == 365
    assert base["ducts"][0]["mesh"]["faces"][-1] == .085
    assert base["ducts"][1]["mesh"]["faces"][-1] == .052
    assert base["port_binding"]["port_set"]["ports"][1]["top_mm"] == 34.597071032
    assert abs(variant["ducts"][-1]["mesh"]["faces"][3] - .103) < 1e-14
    assert abs(base["ducts"][-1]["mesh"]["faces"][3] - .083) < 1e-14
    project_id = project["project_id"]
    runs = args.artifact_root / "exploratory-workflow-v1" / project_id
    serial = runs / "e83ddf4b1249415db6967f3fb717a139"
    first = read(serial / "invocation-001/manifest.json")
    resumed = read(serial / "invocation-002/manifest.json")
    result = read(serial / "result.json")
    assert first["status"] == "CANCELLED_CHECKPOINTED"
    assert first["cycles_completed"] >= 1
    assert resumed["continuation"]["exact_state_restore"] is True
    assert resumed["continuation"]["physical_steps_during_restore"] == 0
    assert resumed["continuation"]["cycles_preserved"] == first["cycles_completed"]
    assert resumed["continuation"]["checkpoint_sha256"] == first["checkpoint_sha256"]
    assert digest(serial / "invocation-001" / first["checkpoint_artifact"]) == first["checkpoint_sha256"]
    assert result["cycles_completed"] == 3
    assert result["classification"] == "MAX_CYCLES_NONCONVERGED"
    assert result["periodicity"] == "NOT_CONVERGED"
    group = args.artifact_root / "dino-parallel-point-sweep-v1" / project_id / "b3c6361ada0b42fab2c3b1be0664f217/dispatch.json"
    dispatch = read(group)
    assert dispatch["status"] == "COMPLETE"
    assert dispatch["worker_count"] == 3
    assert len(dispatch["points"]) == 4
    assert dispatch["elapsed_seconds"] < 120
    evidence = out / "packaged-runs"
    evidence.mkdir(exist_ok=True)
    shutil.copyfile(group, evidence / "dispatch.json")
    verified = []
    for directory in [serial, *(Path(p["run_directory"]) for p in dispatch["points"])]:
        r = read(directory / "result.json")
        cfg = read(directory / "native-configuration.json")
        label = r["bindings"]["variant_label"]
        engine = project["base_engine"] if label == "base" else project["variants"][label]
        expected = resolve_for_operating_point(engine, rpm=r["preflight"]["rpm"])
        # Bind to the frozen distribution's source manifest, not this working
        # tree's file bytes (checkout line endings also affect source hashes).
        expected.pop("identity_sha256")
        expected["source_hashes"] = r["source_hashes"]
        frozen_manifest = Path(package["folder"]) / "_internal/motorsim/build.json"
        assert r["source_hashes"] == {
            **package["build"]["workflow_source_hashes"],
            "dino.package_build_manifest": digest(frozen_manifest),
        }
        assert r["bindings"]["identity_sha256"] == sha256(expected)
        # Entire serialized solver input, not only selected UI fields.
        assert cfg == expected["native_configuration"]
        assert cfg["geometry_identity"].get("spatial_reconstruction_model") is None
        assert "port_root_solver" not in cfg
        assert r["status"] == "COMPLETE" and r["scientific_validation"] == "NOT_CLAIMED"
        assert r["classification"] == "MAX_CYCLES_NONCONVERGED"
        assert digest(directory / r["checkpoint_artifact"]) == r["checkpoint_sha256"]
        manifest_path = directory / r["attempt"] / "manifest.json"
        m = read(manifest_path)
        assert m["wall_s"] <= m["limits"]["wall_seconds"]
        assert m["peak_rss_mib"] < m["limits"]["memory_mib"]
        size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
        assert size < 512 * 1024**2
        target = evidence / directory.name
        target.mkdir(exist_ok=True)
        for name in ("result.json", "run.json", "native-configuration.json"):
            shutil.copyfile(directory / name, target / name)
        for manifest in directory.glob("invocation-*/manifest.json"):
            shutil.copyfile(manifest, target / (manifest.parent.name + "-manifest.json"))
        verified.append(dict(run_id=directory.name, variant=label, rpm=r["preflight"]["rpm"],
            classification=r["classification"], periodicity=r["periodicity"],
            cycles_completed=r["cycles_completed"], wall_s=m["wall_s"], peak_rss_mib=m["peak_rss_mib"],
            artifact_bytes=size, input_sha256=digest(directory / "native-configuration.json"),
            result_sha256=digest(directory / "result.json"), checkpoint_sha256=r["checkpoint_sha256"],
            numerical_model="unchanged first-order; no spatial V1/V2 identity; default bisection"))
    original = read(out.parent / "desktop-product-maturity-v1/historical-gui-export.json")
    exported = read(out / "packaged-historical.json")
    loaded = load_results(out / "packaged-historical.csv")
    assert exported["points"] == original["points"] == loaded["points"]
    assert exported["units"] == original["units"] == loaded["units"]
    assert len(loaded["points"]) == 30
    assert exported["csv_sha256"] == digest(out / "packaged-historical.csv")
    assert digest(Path(package["zip"])) == package["sha256"]
    report = dict(status="PASS", solver_input_exact_match=True, project_values_preserved=True,
        serial_cancel_status=first["status"], restored_cycles=resumed["continuation"]["cycles_preserved"],
        restore_physical_steps=0, parallel_status=dispatch["status"], parallel_wall_s=dispatch["elapsed_seconds"],
        worker_count=3, historical_points=30, historical_exact_roundtrip=True,
        csv_sha256=exported["csv_sha256"], package_sha256=package["sha256"], runs=verified)
    (out / "packaged-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "runs"}))


if __name__ == "__main__":
    main()
