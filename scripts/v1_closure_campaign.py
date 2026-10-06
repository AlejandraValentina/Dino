"""Frozen 20-cycle producer for the two-stroke v1 prime campaigns."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from motorsim.integrated_2t import (  # noqa: E402
    IntegratedEngine2T, audit_integrated_cycle_primary, make_integrated_cycle_primary,
)
from motorsim.periodicity import THRESHOLDS  # noqa: E402
from scripts.produce_integrated_cycle_evidence import advance_to  # noqa: E402

PREREG = ROOT / "results/2t-v1-closure-20261006/campaign-preregistration.json"
CONFIG_ROOT = ROOT / "results/2t-commercial-core-20261002/fixtures/v1-prime-mesh"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(fixture_id: str) -> dict:
    path = CONFIG_ROOT / f"{fixture_id.lower()}-mesh-0.json"
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    engine = IntegratedEngine2T.from_configuration_dict(wrapper["engine_configuration"])
    if engine.configuration_dict() != wrapper["engine_configuration"]:
        raise ValueError(f"{fixture_id}: configuration roundtrip failed")
    return {"path": path, "wrapper": wrapper, "engine": engine}


def run(fixture_id: str, output: Path) -> dict:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    spec = prereg["fixtures"][fixture_id]
    loaded = load(fixture_id)
    wrapper = loaded["wrapper"]
    config = wrapper["engine_configuration"]
    config_hash = sha(canonical(config))
    if config_hash != spec["engine_configuration_sha256"]:
        raise ValueError(f"{fixture_id}: configuration hash is not preregistered")
    if output.exists():
        raise ValueError(f"output exists: {output}")
    output.mkdir(parents=True)
    engine = loaded["engine"]
    runner_sha = sha(Path(__file__).read_bytes())
    rejected: list[dict] = []
    start = engine.snapshot()
    cycle_summaries = []
    restart_snapshot = None
    restart_engine = None
    for cycle in range(1, 21):
        first_rejection = len(rejected)
        advance_to(engine, float(cycle * 360), rejected)
        end = engine.snapshot()
        primary = make_integrated_cycle_primary(
            engine, start, end, cycle,
            rejected_trials=rejected[first_rejection:], runner_sha256=runner_sha)
        audit = audit_integrated_cycle_primary(primary)
        if audit.get("recomputed") is not True:
            raise ValueError(f"{fixture_id}: cycle {cycle} offline audit failed")
        with (output / f"cycle-{cycle:03d}.json.gz").open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                stream.write(canonical(primary))
        cycle_summaries.append({
            "cycle": cycle, "accepted_steps": len(primary["trajectory"]),
            "rejected_trials": len(primary["rejected_trials"]),
            "audit": "PASS",
            "terminal_snapshot_sha256": sha(canonical(end)),
        })
        if cycle == 10:
            restart_snapshot = end
            restart_engine = IntegratedEngine2T.from_configuration_dict(config)
            restart_engine.restore(restart_snapshot)
        if cycle == 11 and restart_engine is not None:
            replay_rejections: list[dict] = []
            advance_to(restart_engine, 11.0 * 360.0, replay_rejections)
            if canonical(restart_engine.snapshot()) != canonical(end):
                raise ValueError(f"{fixture_id}: restart cycle 11 mismatch")
        start = end
    result = {
        "schema": "MOTORSIM_2T_V1_CAMPAIGN_RESULT_V1",
        "status": "PASS",
        "classification": "SYNTHETIC_ASSUMPTION_CONDITIONAL_ON_P4",
        "fixture_id": fixture_id, "mesh_level": 0, "rpm": config["reference_rpm"],
        "horizon_cycles": 20, "restart_cycle": 10,
        "periodicity_detector": "motorsim.periodicity.PeriodicityDetector",
        "periodicity_thresholds": THRESHOLDS,
        "periodicity_status": "NOT_CONVERGENCE_WITHIN_HORIZON",
        "engine_configuration_sha256": config_hash,
        "preregistration_sha256": sha(PREREG.read_bytes()),
        "runner_sha256": runner_sha,
        "restart_cycle_11_exact": True,
        "cycles": cycle_summaries,
    }
    (output / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", choices=("FIXTURE_A_PRIME", "FIXTURE_B_PRIME"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.fixture, (ROOT / args.output).resolve())
    print(json.dumps({"fixture_id": result["fixture_id"], "status": result["status"],
                      "horizon_cycles": result["horizon_cycles"],
                      "periodicity_status": result["periodicity_status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
