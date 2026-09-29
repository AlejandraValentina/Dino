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
    """Reject nonfinite JSON leaves; field validators enforce numeric types."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, (tuple, list)):
        return all(finite(v) for v in value)
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    return False


def number(value, label: str, *, positive: bool = False, nonnegative: bool = False):
    """Validate a JSON number before Python can coerce bool to 0 or 1."""
    require(type(value) in (int, float) and math.isfinite(value), f"MALFORMED_{label}")
    require(not positive or value > 0, f"MALFORMED_{label}")
    require(not nonnegative or value >= 0, f"MALFORMED_{label}")
    return value


def integer(value, label: str, *, positive: bool = False):
    require(type(value) is int and (not positive or value > 0), f"MALFORMED_{label}")
    return value


def numeric_list(value, length: int, label: str) -> None:
    require(type(value) is list and len(value) == length, f"MALFORMED_{label}")
    for item in value:
        number(item, label)


def validate_identity(identity: dict) -> None:
    require(type(identity) is dict, "MALFORMED_IDENTITY")
    integer(identity["mesh"], "MESH", positive=True)
    integer(identity["rpm"], "RPM", positive=True)
    integer(identity["anchor_cycle"], "ANCHOR_CYCLE", positive=True)
    for key in ("configuration_hash", "scientific_contract_id", "solver", "backend",
                "geometry", "operating_point", "cycle_convention"):
        require(type(identity[key]) is str and bool(identity[key]), "MALFORMED_IDENTITY")
    require(type(identity["branch_map"]) is dict
            and all(type(identity["branch_map"].get(k)) is str for k in ("A", "B")),
            "MALFORMED_BRANCH_MAP")


def validate_metric_inputs(row: dict, mesh: int) -> None:
    integer(row["cycle"], "CYCLE", positive=True)
    number(row["begin"], "BEGIN_ANGLE")
    number(row["end"], "END_ANGLE")
    numeric_list(row["state"], 9, "STATE")
    require(type(row["cells"]) is list and len(row["cells"]) == mesh,
            "STATE_OR_MESH_SHAPE_MISMATCH")
    for cell in row["cells"]:
        numeric_list(cell, 4, "CELL")
    number(row["work_indicated_J"], "WORK")
    numeric_list(row["port_integral"], 3, "PORT_INTEGRAL")
    number(row["initial_cylinder_mass"], "INITIAL_CYLINDER_MASS")
    history = row["history"]
    require(type(history) is list and bool(history), "INCOMPLETE_ANGULAR_HISTORY")
    for sample in history:
        number(sample["angle"], "SAMPLE_ANGLE")
        number(sample["p_cyl"], "CYLINDER_PRESSURE")
        sensors = sample["sensors_p_u_M_Y"]
        require(type(sensors) is list and len(sensors) == 3, "SENSOR_SHAPE_MISMATCH")
        for sensor in sensors:
            numeric_list(sensor, 1, "SENSOR_PRESSURE")


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
    require(type(raw) is dict and type(raw["complete"]) is bool,
            "MALFORMED_GATE_INPUTS")
    numeric_list(raw["global_balance"], 3, "GLOBAL_BALANCE")
    segments = raw["segments"]
    require(type(segments) is list and len(segments) == 3, "MISSING_SEGMENTS")
    for segment in segments:
        numeric_list(segment["physical_balance"], 3, "PHYSICAL_BALANCE")
        number(segment["max_global_residual"], "GLOBAL_RESIDUAL", nonnegative=True)
        number(segment["max_stage_residual"], "STAGE_RESIDUAL", nonnegative=True)
        extrema = segment["extrema"]
        for key in ("rho", "p", "T", "Y_min", "Y_max"):
            number(extrema[key], f"EXTREMA_{key}")
        stages = segment["stages"]
        require(type(stages) is list and bool(stages), "MISSING_CFL_STAGES")
        for stage in stages:
            number(stage["dt"], "CFL_DT", positive=True)
            limits = stage["limits"]
            require(type(limits) is list and bool(limits), "MALFORMED_CFL_LIMITS")
            for limit in limits:
                number(limit, "CFL_LIMIT", positive=True)
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
    number(a, "CLAIM_METRIC")
    number(b, "COMPUTED_METRIC")
    return math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-14)


def check_claim(claim: dict, metric: dict, label: str) -> None:
    require(type(claim) is dict and type(claim.get("passed")) is bool
            and claim["passed"] is metric["passed"],
            f"{label}_PASS_CLAIM_MISMATCH")
    if metric.get("status") == "INVALID":
        require(claim.get("status") == "INVALID", f"{label}_INVALID_CLAIM_MISMATCH")
        return
    for key in ("work", "cylinder", "sensor_max", "port"):
        require(near(claim[key], metric[key]), f"{label}_{key}_CLAIM_MISMATCH")
    require(type(claim["sensor"]) is list and len(claim["sensor"]) == 3
            and type(claim["inventories"]) is list and len(claim["inventories"]) == 12,
            f"{label}_CLAIM_VECTOR_SHAPE")
    require(all(near(x, y) for x, y in zip(claim["sensor"], metric["sensor"])),
            f"{label}_SENSOR_CLAIM_MISMATCH")
    require(all(near(x, y) for x, y in zip(claim["inventories"], metric["inventories"])),
            f"{label}_INVENTORY_CLAIM_MISMATCH")
    aliases = {"cylinder_pressure": "cylinder", "sensor_pressure": "sensor",
               "port_mass": "port"}
    for alias, source in aliases.items():
        if alias in claim:
            if source == "sensor":
                numeric_list(claim[alias], 3, f"{label}_{alias}")
                require(all(near(x, y) for x, y in zip(claim[alias], metric[source])),
                        f"{label}_{alias}_CLAIM_MISMATCH")
            else:
                require(near(claim[alias], metric[source]),
                        f"{label}_{alias}_CLAIM_MISMATCH")


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
    validate_identity(row["identity"])
    validate_metric_inputs(row, identity["mesh"])
    require(row["identity"] == identity and row["cycle"] == cycle, "SCIENTIFIC_IDENTITY_MISMATCH")
    require(row["begin"] == 180.+360.*(cycle-1) and row["end"] == 180.+360.*cycle,
            "ANGULAR_CYCLE_MISMATCH")
    return payload, hashlib.sha256(packed).hexdigest()


def validate_detector_snapshot(snap: dict, cycle: int) -> None:
    require(type(snap) is dict, "MALFORMED_DETECTOR_SNAPSHOT")
    integer(snap["last_cycle"], "DETECTOR_CYCLE", positive=True)
    state = snap["state"]
    require(type(state) is dict, "MALFORMED_DETECTOR_STATE")
    integer(state["anchor_cycle"], "DETECTOR_ANCHOR", positive=True)
    for key in ("lag1_streak", "branch_A_streak", "branch_B_streak"):
        integer(state[key], f"DETECTOR_{key.upper()}")
        require(state[key] >= 0, f"MALFORMED_DETECTOR_{key.upper()}")
    if state["detected_period"] is not None:
        integer(state["detected_period"], "DETECTED_PERIOD", positive=True)
        require(state["detected_period"] in (1, 2), "MALFORMED_DETECTED_PERIOD")
    if state["converged_cycle"] is not None:
        integer(state["converged_cycle"], "CONVERGED_CYCLE", positive=True)
        require(state["converged_cycle"] == cycle, "MALFORMED_CONVERGED_CYCLE")
    validate_identity(state["history_identity"])


def audit(root: Path) -> dict:
    try:
        manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
        require(manifest["schema"] == SCHEMA and manifest["contract"] == "G2-v2",
                "INVALID_MANIFEST")
        integer(manifest["max_cycles"], "MAX_CYCLES", positive=True)
        require(type(manifest["thresholds"]) is dict, "MALFORMED_THRESHOLDS")
        for key in EXPECTED_THRESHOLDS:
            number(manifest["thresholds"][key], f"THRESHOLD_{key}", positive=True)
        require(manifest["max_cycles"] == EXPECTED_MAX_CYCLES
                and manifest["thresholds"] == EXPECTED_THRESHOLDS, "CONTRACT_MISMATCH")
        identity = manifest["identity"]
        validate_identity(identity)
        require(identity == EXPECTED_IDENTITY, "SCIENTIFIC_IDENTITY_MISMATCH")
        number(manifest["runtime"]["cfl"], "RUNTIME_CFL", positive=True)
        integer(manifest["runtime"]["workers"], "RUNTIME_WORKERS", positive=True)
        require(manifest["runtime"]["cfl"] == .4
                and manifest["runtime"]["fastmath"] is False
                and manifest["runtime"]["parallel"] is False
                and manifest["runtime"]["workers"] == 1, "RUNTIME_MISMATCH")
        files = sorted(root.glob("checkpoint_cycle*.json.gz"))
        require(bool(files), "MISSING_CHECKPOINTS")
        cycles = [int(p.stem.split("cycle")[1].split(".")[0]) for p in files]
        require(cycles == list(range(1, max(cycles)+1)) and 30 <= max(cycles) <= 400,
                "CYCLE_GAP_OR_OUT_OF_HORIZON")
        source = manifest["source_cycles"]
        require(type(source) is list, "MALFORMED_SEED_ANCESTRY")
        for item in source:
            integer(item["cycle"], "SOURCE_CYCLE", positive=True)
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
            claims = payload["claims"]
            require(type(claims) is dict and type(claims["checks"]) is dict,
                    "MALFORMED_CLAIMS")
            if cycle >= 31:
                integer(claims["cycle"], "CLAIM_CYCLE", positive=True)
                require(claims["cycle"] == cycle and claims["branch"] ==
                        ("A" if cycle % 2 else "B"), "CLAIM_CYCLE_OR_BRANCH_MISMATCH")
                number(claims["elapsed_seconds"], "ELAPSED_SECONDS", nonnegative=True)
            for name, value in gate.items():
                require(claims["checks"].get(name) is value,
                        f"{name}_GATE_CLAIM_MISMATCH")
            m1, m2 = compare(prior, row), compare(prior2, row)
            require(prior is None or prior["end"] == row["begin"], "CYCLE_CONTINUITY_MISMATCH")
            check_claim(claims["lag1"], m1, "LAG1")
            check_claim(claims["lag2"], m2, "LAG2")
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
            validate_detector_snapshot(snap, cycle)
            state = snap["state"]
            if cycle >= 31:
                validate_detector_snapshot({"last_cycle": cycle,
                                            "state": claims["detector"]}, cycle)
                require(claims["detector"] == state, "CLAIM_DETECTOR_STATE_MISMATCH")
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
        integer(producer["last_cycle"], "DECISION_CYCLE", positive=True)
        integer(producer["cycles_executed"], "DECISION_EXECUTED_CYCLES", positive=True)
        integer(producer["max_cycles"], "DECISION_MAX_CYCLES", positive=True)
        require(producer["status"] == status and producer["stop_reason"] == reason
                and producer["last_cycle"] == cycles[-1]
                and producer["cycles_executed"] == cycles[-1]-30
                and producer["max_cycles"] == EXPECTED_MAX_CYCLES
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
