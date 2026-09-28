"""Single-run C3 audit with independent offline momentum reconstruction."""
import json
import math
import statistics
import time
from math import fsum
from pathlib import Path

from dev_orchestrator.p4_sci_04b import EOS, C2_AREA, C2_VOLUME, C2_L_DUCT, solve_c2_one
from dev_orchestrator.reference.exact_riemann import ExactRiemann
from dev_orchestrator.reference.hllc_audit import hllc as audit_hllc

OUT = Path("results/p4-c3-r3-20260928")
CONSERVATION_THRESHOLD = 1e-10  # existing P4/C2 ledger criterion
RESIDUAL_EPSILON = 1e-30


def _minmod(a, b):
    if a == 0.0 or b == 0.0 or (a > 0.0) != (b > 0.0):
        return 0.0
    return a if abs(a) <= abs(b) else b


def reconstruct_external_faces(states, geometry, eos=EOS):
    """Minimal independent B0 reconstruction for the two exterior faces.

    This intentionally duplicates only the MUSCL/minmod stencil needed by the
    C3 fixture.  It does not import or call the production reconstruct().
    The left exterior ghost is outflow (the first cell), and the right one is
    the reflective wall ghost.
    """
    if not states:
        raise ValueError("B0 requires at least one primitive cell")
    if "faces" in geometry and "centers" in geometry:
        faces = geometry["faces"]
        centers = geometry["centers"]
    else:
        # Small synthetic unit-cell fixtures may provide only areas.  Their
        # geometry is intentionally normalized here, without consulting a
        # production mesh or flux field.
        n = len(states)
        faces = [float(i) for i in range(n + 1)]
        centers = [i + 0.5 for i in range(n)]
    first = tuple(states[0])
    last = tuple(states[-1])
    left_ghost = first
    right_ghost = (last[0], -last[1], last[2], last[3])

    def face_pair(i, left, xl, right, xr):
        x = centers[i]
        slopes = [_minmod((v - l) / (x - xl), (r - v) / (xr - x))
                  for l, v, r in zip(left, states[i], right)]
        cell = tuple(states[i])
        left = tuple(v + s * (faces[i] - x) for v, s in zip(cell, slopes))
        right = tuple(v + s * (faces[i + 1] - x) for v, s in zip(cell, slopes))
        downgraded = False
        try:
            # Production reconstruct() validates both reconstructed faces and
            # downgrades the complete cell if either face is inadmissible.
            eos.validate(left)
            eos.validate(right)
        except (ValueError, OverflowError, ZeroDivisionError):
            left = right = cell
            downgraded = True
        return left, right, downgraded

    left_ghost_x = 2.0 * faces[0] - centers[0]
    right_ghost_x = 2.0 * faces[-1] - centers[-1]
    if len(states) == 1:
        left_face, right_face, downgraded = face_pair(
            0, left_ghost, left_ghost_x, right_ghost, right_ghost_x)
        left_downgraded = right_downgraded = downgraded
    else:
        left_face, _, left_downgraded = face_pair(
            0, left_ghost, left_ghost_x, states[1], centers[1])
        _, right_face, right_downgraded = face_pair(
            len(states) - 1, states[-2], centers[-2], right_ghost, right_ghost_x)
    wall_right = (right_face[0], -right_face[1], right_face[2], right_face[3])
    downgraded_cells = []
    if left_downgraded:
        downgraded_cells.append(0)
    if right_downgraded and len(states) - 1 not in downgraded_cells:
        downgraded_cells.append(len(states) - 1)
    return {"interface": {"right": list(left_face)},
            "wall": {"left": list(right_face), "right": list(wall_right)},
            "downgraded": {
                "cells": downgraded_cells,
                "sides": {
                    "interface": {"right": left_downgraded},
                    "wall": {"left": right_downgraded,
                             "right": right_downgraded},
                },
            }}


def _b0_audit_stage(stage, geometry):
    expected = reconstruct_external_faces(stage["primitive"], geometry)
    expected["interface"]["left"] = list(_state_from_chamber(stage["chamber_state"]))
    captured = stage.get("external_faces")
    if captured is None:
        return {"status": "FAIL", "reason": "missing_persisted_external_faces",
                "expected": expected}
    checks = {
        "interface_left": captured["interface"]["left"] == expected["interface"]["left"],
        "interface_right": captured["interface"]["right"] == expected["interface"]["right"],
        "wall_left": captured["wall"]["left"] == expected["wall"]["left"],
        "wall_right": captured["wall"]["right"] == expected["wall"]["right"],
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks, "expected": expected,
            "captured": captured,
            "product_fluxes_used": False}


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
    candidates = []
    for external_time, info in history:
        sample_time = info.get("sample_time_pre_step", external_time)
        if (window[0] <= sample_time <= window[1]
                and info["mass_flux"] > 0.0):
            candidates.append((sample_time, info))
    return (candidates[0], window) if candidates else (None, window)


def _riemann_audit(info):
    # interface_flux_observed is captured from op0, i.e. stage_a.  Keep the
    # independently reconstructed state aligned with that same stage.
    stage = info["audit_stages"]["stage_a"]
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
        "capture_contract": "stage_a conservative/chamber/time and primitive/observed flux all pre-step op0",
    }


def _recompute_stage(stage, geometry):
    primitive = [tuple(w) for w in stage["primitive"]]
    areas = geometry["areas"]
    left_state = _state_from_chamber(stage["chamber_state"])
    left_flux = C2_AREA * _physical_flux(
        ExactRiemann(left_state, primitive[0], EOS).sample(0.0))[1]
    # The production C2 fixture uses an exact reflective wall state, not a
    # static-pressure face.  Rebuild the physical ghost from the last cell and
    # solve that wall Riemann problem independently of productive HLLC.
    last = primitive[-1]
    ghost = (last[0], -last[1], last[2], last[3])
    wall_reference = ExactRiemann(last, ghost, EOS)
    wall_sample = wall_reference.sample(0.0)
    right_flux = areas[-1] * _physical_flux(wall_sample)[1]
    source = fsum(w[2] * (areas[i + 1] - areas[i])
                   for i, w in enumerate(primitive))
    return {"left": left_flux, "right": right_flux, "source": source,
            "momentum_before": fsum(row[1] for row in stage["conservative"]),
            "units": {"face_flux": "N", "source": "N", "momentum": "kg*m/s"}}


def _recompute_stage_b(stage, geometry):
    """Recompute one B2 stage from B0 states and independent B1 HLLC only."""
    b0 = _b0_audit_stage(stage, geometry)
    if b0["status"] != "PASS":
        raise ValueError("B0 audit failed; B1/B2 are not evaluated")
    faces = b0["captured"]
    chamber = _state_from_chamber(stage["chamber_state"])
    interface_right = tuple(faces["interface"]["right"])
    wall_left = tuple(faces["wall"]["left"])
    wall_right = tuple(faces["wall"]["right"])
    interface_flux, interface_waves, interface_reason = audit_hllc(
        chamber, interface_right, EOS)
    wall_flux, wall_waves, wall_reason = audit_hllc(wall_left, wall_right, EOS)
    area_left = geometry["areas"][0]
    area_right = geometry["areas"][-1]
    source = fsum(w[2] * (geometry["areas"][i + 1] - geometry["areas"][i])
                  for i, w in enumerate(stage["primitive"]))
    before = fsum(row[1] for row in stage["conservative"])
    return {
        "b0": b0,
        "left": area_left * interface_flux[1],
        "right": area_right * wall_flux[1],
        "source": source,
        "momentum_before": before,
        "b1": {"interface_waves": interface_waves, "wall_waves": wall_waves,
               "interface_reason": interface_reason, "wall_reason": wall_reason,
               "interface_flux": list(interface_flux), "wall_flux": list(wall_flux)},
        "units": {"face_flux": "N", "source": "N", "momentum": "kg*m/s"},
    }


def _b1_audit_stage(stage, geometry):
    """B1 result for both exterior faces; never reads a product flux field."""
    result = _recompute_stage_b(stage, geometry)
    return {"status": "PASS" if result["b0"]["status"] == "PASS" else "FAIL",
            "reason": "independent HLLC/HLLE over persisted B0 states",
            "product_flux_fields_used": [], "result": result["b1"]}


def _momentum_audit(history, geometry):
    rows = []
    for time_value, info in history:
        stages = info["audit_stages"]
        a = _recompute_stage_b(stages["stage_a"], geometry)
        b = _recompute_stage_b(stages["stage_b"], geometry)
        after = fsum(row[1] for row in stages["after"]["conservative"])
        predicted = 0.5 * stages["stage_a"]["dt"] * (
            a["left"] - a["right"] + a["source"] +
            b["left"] - b["right"] + b["source"])
        observed = after - a["momentum_before"]
        residual = observed - predicted
        relative_residual = abs(residual) / max(abs(predicted), abs(observed),
                                               RESIDUAL_EPSILON)
        rows.append({"time": time_value, "dt": stages["stage_a"]["dt"],
                     "recomputed_stage_a": a, "recomputed_stage_b": b,
                     "momentum_after": after, "predicted_delta": predicted,
                     "observed_delta": observed, "residual": residual,
                     "relative_residual": relative_residual})
    return {
        "status": "METRIC_ONLY",
        "status_reason": "No rigorous IEEE-754 backward-error bound has been derived for the full primitive reconstruction, EOS and HLLC operation graph; no physical tolerance is introduced.",
        "control_volume": "all duct cells, chamber excluded",
        "sign_convention": "+x duct direction; left enters, right exits; source=sum[p_i*(A_right-A_left)]",
        "interior_faces": "telescoped by control-volume definition; no productive interior flux array is read",
        "independent_inputs": ["stored conservative states", "stored primitive states",
                               "persisted B0 external face states", "stored areas/faces/volumes", "stage dt"],
        "product_field_names_used": [], "steps": len(rows), "rows": rows,
        "max_abs_residual": max((abs(r["residual"]) for r in rows), default=0.0),
        "relative_residual_scale": "max(abs(predicted_delta), abs(observed_delta), epsilon)",
        "relative_residual_epsilon": RESIDUAL_EPSILON,
        "max_relative_residual": max((r["relative_residual"] for r in rows),
                                      default=0.0),
        "median_relative_residual": statistics.median(
            [r["relative_residual"] for r in rows]) if rows else 0.0,
        "rounding_policy": {
            "classification": "metric-only",
            "residual_is": "observed SSPRK2 momentum delta minus independently recomputed B1 face/source prediction",
            "physical_threshold": None,
            "missing_justification": "operation-count and conditioning analysis covering EOS primitive conversion, MUSCL minmod branches, HLLC waves, area scaling and fsum order",
        },
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
    capture_contract = {
        "stage_a": "pre-step cells/z/t copied before commit; primitive and observed flux from op0",
        "stage_b": "cells1/z1/op1 primitive",
        "after": "cells_new/z_new/ws_new",
        "invalidated_revision": "174b261",
        "invalidated_reason": "stage_a conservative/chamber captured post-step while primitive/flux were pre-step",
    }
    _write(OUT / "configuration.json", {"N": 100, "CFL": 0.2, "t_final": 0.004,
        "area": C2_AREA, "duct_length": C2_L_DUCT, "backend": "existing C2 fixture",
        "acquisition": "single focal run", "expected_return": expected_time,
        "return_window": window, "conservation_threshold": CONSERVATION_THRESHOLD,
        "capture_contract": capture_contract})
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
        "single_run": True, "wall_seconds": time.perf_counter() - started,
        "capture_contract": capture_contract,
        "e13": "NOT_EXECUTED_C3_NOT_PASS",
        "p9": "STOPPED"})


if __name__ == "__main__":
    main()
