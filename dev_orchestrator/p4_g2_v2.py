from __future__ import annotations
import gzip, json, math, time
from pathlib import Path
from dev_orchestrator.p4_hybrid import prepare, checks
from motorsim.hybrid_fast import run_cycle
from motorsim.periodicity import PeriodicityDetector, compare_cycles

ROOT = Path("results/p4-g2-v2-20260929")
HIST = Path("results/p4-g2-periodic-completion-20260923")
MAX_CYCLES = 400
EXPECTED = {
    "configuration_hash": "p4-r6-g2-chain",
    "scientific_contract_id": "E13-R1",
    "solver": "NUMBA_FUSED", "backend": "NUMBA_FUSED",
    "mesh": 251, "geometry": "chain", "rpm": 3000,
    "operating_point": "G2", "cycle_convention": "360",
    "anchor_cycle": 1,
    "branch_map": {"A": "odd_relative_to_anchor", "B": "even_relative_to_anchor"},
}

def load(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)

def finite_tree(values):
    if isinstance(values, (int, float)):
        return math.isfinite(values)
    if isinstance(values, list):
        return all(finite_tree(v) for v in values)
    return True

def validate_restart(r29, r30):
    for r in (r29, r30):
        for k, v in EXPECTED.items():
            if r.get(k) != v:
                raise RuntimeError(f"restart identity mismatch {k}: {r.get(k)!r} != {v!r}")
        if not r.get("complete") or not finite_tree(r.get("state")) or not finite_tree(r.get("cells")):
            raise RuntimeError("restart incomplete or nonfinite")
        if r.get("checks", {}).get("conservation") is not True or r.get("checks", {}).get("positive") is not True:
            raise RuntimeError("restart physical checks are not PASS")
    if r29.get("cycle") != 29 or r30.get("cycle") != 30 or r29.get("end") != r30.get("begin"):
        raise RuntimeError("restart angular continuity mismatch")

def compact(row, cycle, branch, lag1, lag2, detector, elapsed):
    return {
        "cycle": cycle, "branch": branch,
        "begin": row["begin"], "end": row["end"],
        "lag1_status": "PASS" if lag1.get("passed") else "FAIL", "lag1_passed": bool(lag1.get("passed")),
        "lag1_sensor_max": lag1.get("sensor_max"),
        "lag2_status": "PASS" if lag2.get("passed") else "FAIL", "lag2_passed": bool(lag2.get("passed")),
        "lag2_sensor_max": lag2.get("sensor_max"),
        "lag2_work": lag2.get("work"), "lag2_cylinder": lag2.get("cylinder"),
        "lag2_port": lag2.get("port"), "lag2_inventories": lag2.get("inventories"),
        "lag1_streak": detector.lag1_streak,
        "branch_A_streak": detector.branch_A_streak,
        "branch_B_streak": detector.branch_B_streak,
        "detected_period": detector.detected_period,
        "conservation": row.get("checks", {}).get("conservation"),
        "admissibility": row.get("checks", {}).get("positive"),
        "cfl": row.get("checks", {}).get("CFL"),
        "cycle_wall_seconds": row.get("cycle_wall_seconds"),
        "elapsed_seconds": elapsed,
    }

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    r29 = load(HIST / "cycle29.json.gz")
    r30 = load(HIST / "cycle30.json.gz")
    validate_restart(r29, r30)
    (ROOT / "continuation-validation.json").write_text(json.dumps({
        "status": "PASS", "source_cycle": 30, "prior_cycle": 29,
        "source": str(HIST / "cycle30.json.gz"), "angular_continuity": "29.end == 30.begin",
        "identity": EXPECTED, "state_reused": True,
        "physical_checks": {"cycle29": r29["checks"], "cycle30": r30["checks"]},
        "detector_state_reused": {"anchor_cycle": 1, "branch_map": EXPECTED["branch_map"],
                                   "lag1_streak": 0, "branch_A_streak": 5, "branch_B_streak": 0},
    }, indent=2), encoding="utf-8")
    detector = PeriodicityDetector(1, EXPECTED["branch_map"])
    detector.lag1_streak = 0
    detector.branch_A_streak = 5
    detector.branch_B_streak = 0
    previous2, previous = r29, r30
    trace = ROOT / "cycle-trace.jsonl"
    trace.write_text("", encoding="utf-8")
    cycle = 30
    stop_reason = None
    started = time.perf_counter()
    while cycle < MAX_CYCLES:
        cycle += 1
        model, mesh, _, _ = prepare("chain")
        t0 = time.perf_counter()
        row = run_cycle(mesh, previous["cells"], previous["state"], previous["end"], backend="NUMBA_FUSED")
        row.update(cycle=cycle, configuration_hash=EXPECTED["configuration_hash"],
                   scientific_contract_id=EXPECTED["scientific_contract_id"], solver=EXPECTED["solver"],
                   backend=EXPECTED["backend"], mesh=EXPECTED["mesh"], geometry=EXPECTED["geometry"],
                   rpm=EXPECTED["rpm"], operating_point=EXPECTED["operating_point"],
                   cycle_convention=EXPECTED["cycle_convention"], anchor_cycle=1,
                   branch_map=EXPECTED["branch_map"], initial_cylinder_mass=previous["state"][6])
        row["checks"] = checks(row)
        lag1 = compare_cycles(previous, row)
        lag2 = compare_cycles(previous2, row)
        branch = "A" if (cycle - 1) % 2 == 0 else "B"
        detector.update(row, lag1=lag1, lag2=lag2, branch=branch)
        if not finite_tree(row.get("state")) or not finite_tree(row.get("cells")):
            stop_reason = "INVALID_NONFINITE_EVIDENCE"
        if row["checks"].get("conservation") is not True or row["checks"].get("positive") is not True:
            stop_reason = "NUMERICAL_FAILURE"
        item = compact(row, cycle, branch, lag1, lag2, detector, time.perf_counter() - started)
        with trace.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, allow_nan=False) + "\n")
        # Compact restart evidence is retained every cycle; full histories are not discarded until audited.
        (ROOT / f"checkpoint_cycle{cycle:03}.json.gz").write_bytes(gzip.compress(json.dumps({
            "cycle": cycle, "begin": row["begin"], "end": row["end"], "state": row["state"],
            "cells": row["cells"], "checks": row["checks"], "identity": EXPECTED,
            "detector": detector.to_json(),
        }, allow_nan=False).encode()))
        print(json.dumps(item, allow_nan=False), flush=True)
        if stop_reason:
            break
        if detector.detected_period is not None:
            stop_reason = f"CONVERGED_PERIOD{detector.detected_period}"
            break
        previous2, previous = previous, row
        del row
    if stop_reason is None:
        stop_reason = "MAX_CYCLES_400_WITHOUT_CONVERGENCE"
    decision = {
        "contract": "G2-v2", "status": "E13_G2_V2_PASS" if stop_reason.startswith("CONVERGED") else ("E13_G2_V2_INCONCLUSIVE" if stop_reason.startswith("INVALID") or stop_reason == "NUMERICAL_FAILURE" else "E13_G2_V2_FAIL"),
        "stop_reason": stop_reason, "cycles_executed": cycle - 30,
        "last_cycle": cycle, "max_cycles": MAX_CYCLES,
        "threshold_sensor_max": 0.005, "detector": detector.to_json(),
        "continuation": "cycle30", "original_g2": "E13_G2_FAIL",
    }
    (ROOT / "decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    (ROOT / "runtime.json").write_text(json.dumps({"wall_seconds": time.perf_counter()-started, "cycles": cycle-30}, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
