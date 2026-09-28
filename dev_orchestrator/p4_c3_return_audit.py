"""Single-run C3 audit with independent offline momentum reconstruction."""
import json
import math
import time
from math import fsum
from pathlib import Path

from dev_orchestrator.p4_sci_04b import EOS, C2_AREA, C2_VOLUME, C2_L_DUCT, solve_c2_one
from dev_orchestrator.reference.exact_riemann import ExactRiemann

OUT = Path("results/p4-c3-r3-20260928")
CONSERVATION_THRESHOLD = 1e-10  # existing P4/C2 ledger criterion


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _physical_flux(state):
    rho, velocity, pressure, species = state
    rho_e = EOS.conservative(state)[2]
    return [rho * velocity, rho * velocity * velocity + pressure,
            velocity * (rho_e + pressure), rho * velocity * species]


def _relative_error(observed, expected):
    errors = [abs(a - b) / max(abs(a), abs(b), 1.0)
              for a, b in zip(observed, expected)]
    return {"components": errors, "max": max(errors)}


def _state_from_chamber(chamber):
    mass, energy, fresh = chamber
    return (mass / C2_VOLUME, 0.0, (EOS.gamma - 1.0) * energy / C2_VOLUME,
            fresh / mass)


def _select_return(history, expected_time):
    window = (0.5 * expected_time, 1.5 * expected_time)
    candidates = [row for row in history
                  if window[0] <= row[0] <= window[1]
                  and row[1]["mass_flux"] > 0.0]
    return (candidates[0], window) if candidates else (None, window)


def _riemann_audit(info):
    stage = info["audit_stages"]["stage_b"]
    left = _state_from_chamber(stage["chamber_state"])
    right = tuple(stage["primitive"][0])
    reference = ExactRiemann(left, right, EOS)
    sampled = reference.sample(0.0)
    expected_per_area = _physical_flux(sampled)
    observed = list(info["interface_flux_observed"])
    expected = [C2_AREA * x for x in expected_per_area]
    return {
        "status": "INCONCLUSIVE",
        "status_reason": "No approved quantitative HLLC-vs-exact equality threshold was found; errors are diagnostic only.",
        "reference_module": "dev_orchestrator.reference.exact_riemann.ExactRiemann",
        "reference_independent_of_productive_hllc": True,
        "productive_fixture_executed": True,
        "left_state": list(left), "right_state": list(right),
        "normal": info["interface_normal"], "area_m2": info["interface_area"],
        "sample_xi": 0.0,
        "exact_star": {"p": reference.pstar, "u": reference.ustar,
                        "sample": list(sampled), "residual": reference.residual},
        "flux_expected_area_integrated": expected,
        "flux_observed_area_integrated": observed,
        "relative_error": _relative_error(observed, expected),
    }


def _recompute_stage(stage, geometry):
    primitive = [tuple(w) for w in stage["primitive"]]
    areas = geometry["areas"]
    left_state = _state_from_chamber(stage["chamber_state"])
    left_flux = C2_AREA * _physical_flux(
        ExactRiemann(left_state, primitive[0], EOS).sample(0.0))[1]
    right_flux = areas[-1] * primitive[-1][2]
    source = fsum(w[2] * (areas[i + 1] - areas[i])
                   for i, w in enumerate(primitive))
    return {"left": left_flux, "right": right_flux, "source": source,
            "momentum_before": fsum(row[1] for row in stage["conservative"]),
            "units": {"face_flux": "N", "source": "N", "momentum": "kg*m/s"}}


def _momentum_audit(history, geometry):
    rows = []
    for time_value, info in history:
        stages = info["audit_stages"]
        a = _recompute_stage(stages["stage_a"], geometry)
        b = _recompute_stage(stages["stage_b"], geometry)
        after = fsum(row[1] for row in stages["after"]["conservative"])
        predicted = 0.5 * stages["stage_a"]["dt"] * (
            a["left"] - a["right"] + a["source"] +
            b["left"] - b["right"] + b["source"])
        observed = after - a["momentum_before"]
        rows.append({"time": time_value, "dt": stages["stage_a"]["dt"],
                     "recomputed_stage_a": a, "recomputed_stage_b": b,
                     "momentum_after": after, "predicted_delta": predicted,
                     "observed_delta": observed, "residual": observed - predicted})
    return {
        "status": "INCONCLUSIVE",
        "status_reason": "No approved quantitative independent momentum-closure threshold was found; reconstructed errors are diagnostic only.",
        "control_volume": "all duct cells, chamber excluded",
        "sign_convention": "+x duct direction; left enters, right exits; source=sum[p_i*(A_right-A_left)]",
        "independent_inputs": ["stored conservative states", "stored primitive states",
                               "stored areas/faces/volumes", "stage dt"],
        "product_field_names_used": [], "steps": len(rows), "rows": rows,
        "max_abs_residual": max((abs(r["residual"]) for r in rows), default=0.0),
    }


def classify(return_ok, conservation_ok, admissibility_ok, riemann, momentum):
    if not return_ok or not conservation_ok or not admissibility_ok:
        return "P4_SCI_C3_FAIL"
    if riemann["status"] == "PASS" and momentum["status"] == "PASS":
        return "P4_SCI_C3_PASS"
    return "P4_SCI_C3_INCONCLUSIVE"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expected_time = 2.0 * C2_L_DUCT / math.sqrt(
        EOS.gamma * 100000.0 / (100000.0 / (EOS.R * 300.0)))
    started = time.perf_counter()
    result = solve_c2_one(100, 0.2, 200000.0, 400.0, 0.5,
                          100000.0, 300.0, 0.2, t_final=0.004)
    selected, window = _select_return(result["interface_history"], expected_time)
    return_ok = selected is not None
    if selected is None:
        selected_time, selected_info = None, None
        riemann = {"status": "INCONCLUSIVE", "status_reason": "No admissible return sample in preregistered window."}
    else:
        selected_time, selected_info = selected
        riemann = _riemann_audit(selected_info)
    momentum = _momentum_audit(result["interface_history"], result["audit_geometry"])
    conservation_ok = result["max_global_resid"] <= CONSERVATION_THRESHOLD
    admissibility_ok = result["status"] == "completed"
    classification = classify(return_ok, conservation_ok, admissibility_ok, riemann, momentum)
    _write(OUT / "configuration.json", {"N": 100, "CFL": 0.2, "t_final": 0.004,
        "area": C2_AREA, "duct_length": C2_L_DUCT, "backend": "existing C2 fixture",
        "acquisition": "single focal run", "expected_return": expected_time,
        "return_window": window, "conservation_threshold": CONSERVATION_THRESHOLD})
    _write(OUT / "return_snapshot.json", {"status": "PASS" if return_ok else "FAIL",
        "time": selected_time, "interface": selected_info,
        "selection": "first admissible sample in window with positive mass flux"})
    _write(OUT / "exact_riemann_comparison.json", riemann)
    _write(OUT / "momentum_control_volume.json", momentum)
    _write(OUT / "conservation.json", {"max_global_resid": result["max_global_resid"],
        "admissibility": admissibility_ok, "status": "PASS" if conservation_ok else "FAIL",
        "threshold": CONSERVATION_THRESHOLD})
    _write(OUT / "decision.json", {"classification": classification,
        "return_snapshot": "PASS" if return_ok else "FAIL",
        "conservation": "PASS" if conservation_ok else "FAIL",
        "admissibility": "PASS" if admissibility_ok else "FAIL",
        "exact_riemann": riemann["status"], "momentum_balance": momentum["status"],
        "single_run": True, "wall_seconds": time.perf_counter() - started})


if __name__ == "__main__":
    main()
