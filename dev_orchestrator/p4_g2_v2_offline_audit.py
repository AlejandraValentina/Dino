"""Independent offline E13/G2-v2 decision from persisted scalar and angular data.

This intentionally does not import the acquisition runner, product comparator,
product detector, product checks, or solver. Recorded PASS flags are assertions
to cross-check, never inputs to the decision.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import gzip
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "G2_V2_DURABLE_V1"
DETECTOR_SCHEMA = "E13_R1_DETECTOR_V1"
EXPECTED_THRESHOLDS = {"work": .005, "cylinder": .005, "sensor_max": .005,
                       "port": .002, "inventories": .002}
EXPECTED_MAX_CYCLES = 400
CONSERVATION_LIMIT = 1e-10
EXPECTED_IDENTITY = {
    "configuration_hash": "p4-r6-g2-chain", "scientific_contract_id": "E13-R1",
    "solver": "NUMBA_FUSED", "backend": "NUMBA_FUSED", "mesh": 251,
    "geometry": "chain", "rpm": 3000, "operating_point": "G2",
    "cycle_convention": "360", "anchor_cycle": 1,
    "branch_map": {"A": "odd_relative_to_anchor", "B": "even_relative_to_anchor"},
}


class EvidenceError(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceError(reason)


def finite(value) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, (tuple, list)):
        return all(finite(v) for v in value)
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    return False


def ratio(a: float, b: float, floor: float = 0.) -> float:
    return abs(a-b) / max(abs(a), abs(b), floor)


def sampled(record: dict, field: str, sensor: int | None = None) -> list[float]:
    history = record["history"]
    require(bool(history), "INCOMPLETE_ANGULAR_HISTORY")
    phases = [h["angle"]-record["begin"] for h in history]
    require(phases[0] <= .5 and phases[-1] == 360., "INCOMPLETE_ANGULAR_HISTORY")
    require(all(a < b for a, b in zip(phases, phases[1:])), "NONMONOTONE_ANGULAR_HISTORY")
    values = ([h[field] for h in history] if sensor is None
              else [h["sensors_p_u_M_Y"][sensor][0] for h in history])
    output = []
    for i in range(1, 721):
        phase = i * .5
        j = bisect_right(phases, phase)
        if j == 0:
            output.append(values[0])
        elif j == len(phases):
            output.append(values[-1])
        else:
            weight = (phase-phases[j-1])/(phases[j]-phases[j-1])
            output.append(values[j-1]+(values[j]-values[j-1])*weight)
    return output


def pressure_gap(a: dict, b: dict, field: str, sensor: int | None = None) -> float:
    old = sampled(a, field, sensor)
    new = sampled(b, field, sensor)
    return max(abs(x-y) for x, y in zip(old, new))/max(abs(x) for x in old+new)


def compare(a: dict | None, b: dict) -> dict:
    if a is None:
        return {"status": "INVALID", "reason": "MISSING_PREVIOUS_CYCLE", "passed": False}
    old, new = a["state"], b["state"]
    inv = []
    for k in (0, 3, 6):
        inv.extend((ratio(old[k], new[k]), ratio(old[k+1], new[k+1]),
                    abs(old[k+2]/old[k]-new[k+2]/new[k])))
    a_pipe = [sum(c[j] for c in a["cells"]) for j in (0, 2, 3)]
    b_pipe = [sum(c[j] for c in b["cells"]) for j in (0, 2, 3)]
    inv.extend((ratio(a_pipe[0], b_pipe[0]), ratio(a_pipe[1], b_pipe[1]),
                abs(a_pipe[2]-b_pipe[2])/max(a_pipe[0], b_pipe[0])))
    sensors = [pressure_gap(a, b, "sensors_p_u_M_Y", sensor=i) for i in range(3)]
    metrics = {"work": ratio(a["work_indicated_J"], b["work_indicated_J"], 1.),
               "cylinder": pressure_gap(a, b, "p_cyl"), "sensor": sensors,
               "sensor_max": max(sensors),
               "port": ratio(a["port_integral"][0], b["port_integral"][0],
                             b["initial_cylinder_mass"]),
               "inventories": inv}
    metrics["passed"] = (metrics["work"] <= EXPECTED_THRESHOLDS["work"]
                         and metrics["cylinder"] <= EXPECTED_THRESHOLDS["cylinder"]
                         and metrics["sensor_max"] <= EXPECTED_THRESHOLDS["sensor_max"]
                         and metrics["port"] <= EXPECTED_THRESHOLDS["port"]
                         and max(inv) <= EXPECTED_THRESHOLDS["inventories"])
    return metrics


def gates(inputs: dict) -> dict:
    raw = inputs["gate_inputs"]
    segments = raw["segments"]
    require(len(segments) == 3, "MISSING_SEGMENTS")
    require(all(bool(s["stages"]) for s in segments), "MISSING_CFL_STAGES")
    complete = raw["complete"] is True
    balance = raw["global_balance"]
    conservation = (isinstance(balance, list) and len(balance) == 3
                    and max(abs(v) for v in balance) <= CONSERVATION_LIMIT
                    and all(max(abs(v) for v in s["physical_balance"]) <= CONSERVATION_LIMIT
                            and s["max_global_residual"] <= CONSERVATION_LIMIT
                            and s["max_stage_residual"] <= CONSERVATION_LIMIT
                            for s in segments))
    positive = all(min(s["extrema"][k] for k in ("rho", "p", "T")) > 0
                   and s["extrema"]["Y_min"] >= 0
                   and s["extrema"]["Y_max"] <= 1 for s in segments)
    cfl = all(stage["dt"] <= min(stage["limits"])
              for segment in segments for stage in segment["stages"])
    return {"complete": complete, "conservation": conservation,
            "positive": positive, "CFL": cfl}


def near(a, b) -> bool:
    return math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-14)


def check_claim(claim: dict, metric: dict, label: str) -> None:
    require(isinstance(claim, dict) and claim.get("passed") is metric["passed"],
            f"{label}_PASS_CLAIM_MISMATCH")
    if metric.get("status") == "INVALID":
        require(claim.get("status") == "INVALID", f"{label}_INVALID_CLAIM_MISMATCH")
        return
    for key in ("work", "cylinder", "sensor_max", "port"):
        require(near(claim[key], metric[key]), f"{label}_{key}_CLAIM_MISMATCH")
    require(len(claim["sensor"]) == 3 and len(claim["inventories"]) == 12,
            f"{label}_CLAIM_VECTOR_SHAPE")
    require(all(near(x, y) for x, y in zip(claim["sensor"], metric["sensor"])),
            f"{label}_SENSOR_CLAIM_MISMATCH")
    require(all(near(x, y) for x, y in zip(claim["inventories"], metric["inventories"])),
            f"{label}_INVENTORY_CLAIM_MISMATCH")


def read_checkpoint(root: Path, cycle: int, parent_sha: str | None, identity: dict) -> tuple[dict, str]:
    path = root / f"checkpoint_cycle{cycle:03}.json.gz"
    packed = path.read_bytes()
    payload = json.loads(gzip.decompress(packed))
    require(payload["schema"] == SCHEMA and finite(payload), "INVALID_CHECKPOINT_SCHEMA_OR_NONFINITE")
    require(payload["parent_sha256"] == parent_sha, "BROKEN_CHECKPOINT_ANCESTRY")
    row = payload["inputs"]
    required = ("state", "cells", "history", "work_indicated_J", "port_integral",
                "initial_cylinder_mass", "gate_inputs", "cycle", "begin", "end", "identity")
    require(all(key in row for key in required), "MISSING_CONTRACT_INPUT")
    require(row["identity"] == identity and row["cycle"] == cycle, "SCIENTIFIC_IDENTITY_MISMATCH")
    require(row["begin"] == 180.+360.*(cycle-1) and row["end"] == 180.+360.*cycle,
            "ANGULAR_CYCLE_MISMATCH")
    require(len(row["state"]) == 9 and len(row["cells"]) == identity["mesh"],
            "STATE_OR_MESH_SHAPE_MISMATCH")
    require(all(len(h["sensors_p_u_M_Y"]) == 3 for h in row["history"]),
            "SENSOR_SHAPE_MISMATCH")
    return payload, hashlib.sha256(packed).hexdigest()


def audit(root: Path) -> dict:
    try:
        manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
        require(manifest["schema"] == SCHEMA and manifest["contract"] == "G2-v2",
                "INVALID_MANIFEST")
        require(manifest["max_cycles"] == EXPECTED_MAX_CYCLES
                and manifest["thresholds"] == EXPECTED_THRESHOLDS, "CONTRACT_MISMATCH")
        identity = manifest["identity"]
        require(identity == EXPECTED_IDENTITY, "SCIENTIFIC_IDENTITY_MISMATCH")
        require(manifest["runtime"]["cfl"] == .4
                and manifest["runtime"]["fastmath"] is False
                and manifest["runtime"]["parallel"] is False
                and manifest["runtime"]["workers"] == 1, "RUNTIME_MISMATCH")
        files = sorted(root.glob("checkpoint_cycle*.json.gz"))
        cycles = [int(p.stem.split("cycle")[1].split(".")[0]) for p in files]
        require(cycles == list(range(1, max(cycles)+1)) and 30 <= max(cycles) <= 400,
                "CYCLE_GAP_OR_OUT_OF_HORIZON")
        source = manifest["source_cycles"]
        require([x["cycle"] for x in source] == list(range(1, 31)), "SEED_ANCESTRY_GAP")
        prior2 = prior = None
        parent_sha = None
        lag1_streak = a_streak = b_streak = 0
        detected = converged_cycle = None
        trace = []
        for cycle in cycles:
            payload, parent_sha = read_checkpoint(root, cycle, parent_sha, identity)
            if cycle <= 30:
                require(payload["source_sha256"] == source[cycle-1]["source_sha256"]
                        and parent_sha == source[cycle-1]["checkpoint_sha256"],
                        "SEED_SOURCE_OR_CHECKPOINT_HASH_MISMATCH")
            else:
                require(payload["source_sha256"] is None, "NEW_CYCLE_HAS_HISTORICAL_SOURCE")
            row = payload["inputs"]
            gate = gates(row)
            for name, value in gate.items():
                require(payload["claims"]["checks"].get(name) is value,
                        f"{name}_GATE_CLAIM_MISMATCH")
            m1, m2 = compare(prior, row), compare(prior2, row)
            require(prior is None or prior["end"] == row["begin"], "CYCLE_CONTINUITY_MISMATCH")
            check_claim(payload["claims"]["lag1"], m1, "LAG1")
            check_claim(payload["claims"]["lag2"], m2, "LAG2")
            branch = "A" if cycle % 2 else "B"
            require(all(gate.values()), "PHYSICAL_GATE_FAILED")
            lag1_streak = lag1_streak+1 if m1["passed"] else 0
            if branch == "A":
                a_streak = a_streak+1 if m2["passed"] else 0
            else:
                b_streak = b_streak+1 if m2["passed"] else 0
            if lag1_streak >= 3:
                detected, converged_cycle = 1, cycle
            elif a_streak >= 3 and b_streak >= 3:
                detected, converged_cycle = 2, cycle
            snap = payload["detector"]
            state = snap["state"]
            require(snap["schema"] == DETECTOR_SCHEMA and snap["last_cycle"] == cycle
                    and snap["last_branch"] == branch, "DETECTOR_SNAPSHOT_IDENTITY_MISMATCH")
            require((state["lag1_streak"], state["branch_A_streak"], state["branch_B_streak"],
                     state["detected_period"], state["converged_cycle"]) ==
                    (lag1_streak, a_streak, b_streak, detected, converged_cycle),
                    "DETECTOR_STATE_MISMATCH")
            require(state["history_identity"] == identity
                    and state["anchor_cycle"] == 1 and state["branch_map"] == identity["branch_map"],
                    "DETECTOR_SCIENTIFIC_IDENTITY_MISMATCH")
            check_claim(snap["last_lag1"], m1, "DETECTOR_LAG1")
            check_claim(snap["last_lag2"], m2, "DETECTOR_LAG2")
            check_claim(state["last_metrics"], m1, "DETECTOR_LAST_METRICS")
            if cycle == 30:
                seed_file = root/"seed-detector-cycle030.json"
                require(sha(seed_file) == manifest["seed_detector_sha256"]
                        and json.loads(seed_file.read_text(encoding="utf-8")) == snap,
                        "SEED_DETECTOR_MISMATCH")
            if cycle >= 31:
                trace.append({"cycle": cycle, "branch": branch,
                              "lag1_passed": m1["passed"], "lag2_passed": m2["passed"],
                              "lag2_sensor_max": m2["sensor_max"],
                              "lag2_work": m2["work"], "lag2_cylinder": m2["cylinder"],
                              "lag2_port": m2["port"],
                              "lag2_inventories_max": max(m2["inventories"]),
                              "CFL": gate["CFL"], "conservation": gate["conservation"],
                              "admissibility": gate["positive"],
                              "lag1_streak": lag1_streak, "branch_A_streak": a_streak,
                              "branch_B_streak": b_streak, "detected_period": detected})
            require(detected is None or cycle == cycles[-1], "EXECUTION_AFTER_FIRST_CONVERGENCE")
            prior2, prior = prior, row
        if detected is not None:
            status = "E13_G2_V2_PASS"
            reason = f"CONVERGED_PERIOD{detected}"
        elif cycles[-1] == 400:
            status, reason = "E13_G2_V2_FAIL", "MAX_CYCLES_400_WITHOUT_CONVERGENCE"
        else:
            raise EvidenceError("INCOMPLETE_HORIZON_WITHOUT_CONVERGENCE")
        producer = json.loads((root/"decision.json").read_text(encoding="utf-8"))
        require(producer["status"] == status and producer["stop_reason"] == reason
                and producer["last_cycle"] == cycles[-1]
                and producer["closing_checkpoint_sha256"] == parent_sha,
                "PRODUCER_DECISION_MISMATCH")
        return {"classification": status, "reason": reason, "last_cycle": cycles[-1],
                "detected_period": detected, "branch_A_streak": a_streak,
                "branch_B_streak": b_streak, "closing_checkpoint_sha256": parent_sha,
                "trace": trace, "audit_method": "offline independent formulae from durable inputs"}
    except (EvidenceError, FileNotFoundError, KeyError, IndexError, TypeError,
            ValueError, ZeroDivisionError, OverflowError) as exc:
        return {"classification": "E13_G2_V2_INCONCLUSIVE", "reason": str(exc),
                "audit_method": "offline independent formulae from durable inputs"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["classification"] == "E13_G2_V2_PASS" else 1)
