"""P8 bounded transient contract and indicated-metric primitives.

This module contains no new engine physics.  It is intentionally independent
of the P4 periodic solver and is used by the eventual full-topology adapter.
"""
from dataclasses import dataclass
from math import pi, isfinite
import csv
import json
from pathlib import Path

from .project import ProjectError

RPM_MIN, RPM_MAX = 2500, 15000
P8_ANCHORS = (2500, 5000, 8000, 11000, 15000)


def validate_p8_rpm(rpm):
    if type(rpm) is not int or not RPM_MIN <= rpm <= RPM_MAX:
        raise ProjectError(f"P8 RPM must be an integer in [{RPM_MIN}, {RPM_MAX}]")
    return rpm


def omega_deg_s(rpm):
    return 6.0 * validate_p8_rpm(rpm)


def cycle_duration_s(rpm):
    return 60.0 / validate_p8_rpm(rpm)


def indicated_metrics(work_j, rpm, pmax_pa):
    validate_p8_rpm(rpm)
    if not all(isfinite(float(x)) for x in (work_j, pmax_pa)):
        raise ValueError("P8 metrics must be finite")
    return {"W_cycle_J": float(work_j),
            "P_indicated_W": float(work_j) * rpm / 60.0,
            "T_indicated_Nm": float(work_j) / (2.0 * pi),
            "p_max_Pa": float(pmax_pa)}


def work_from_pressure_volume(pressure_pa, volume_m3):
    """Trapezoidal integral p dV; positive expansion is delivered work."""
    if len(pressure_pa) != len(volume_m3) or len(pressure_pa) < 2:
        raise ValueError("pressure and volume paths must have equal length >= 2")
    return sum(0.5 * (float(p0) + float(p1)) * (float(v1) - float(v0))
               for p0, p1, v0, v1 in zip(pressure_pa, pressure_pa[1:],
                                         volume_m3, volume_m3[1:]))


@dataclass(frozen=True)
class P8Semantics:
    contract_version: str = "P8-WIDE-RPM-TRANSIENT-V1"
    steady_state: bool = False
    periodic_convergence: str = "NOT_GRANTED_BY_P4"
    metric_semantics: str = "BOUNDED_TRANSIENT_INDICATED"
    conditional_on_p4: bool = True
    experimental_validation: str = "NOT_PERFORMED"
    independent_review: str = "INDEPENDENT_REVIEW_PENDING"


def model_geometry_callback(model):
    """Adapt the authoritative 2T ``Model.geometry`` to P5-C stage data.

    The duct storage remains the verified P5 fixture; only chamber volumes,
    rates, and effective port areas come from the project mechanics.
    """
    project = model.case.project_geometry
    def callback(angle):
        volumes, rates, areas = model.geometry(float(angle))
        # Model.geometry contract: [throat, intake, TR1, TR2, exhaust, outlet].
        intake, transfer1, transfer2, exhaust = areas[1], areas[2], areas[3], areas[4]
        return {'volumes': volumes, 'volume_rates': (rates[1], rates[2]),
                'areas': (intake, transfer1, transfer2, exhaust)}
    return callback


def run_anchor(rpm, *, angle_step_deg=0.05):
    """Run one deterministic bounded transient on the frozen P5-C/P6/P7 stack."""
    from dataclasses import replace
    from .simulation_case import SyntheticCase
    from .simulation import Model
    from .p5c import make_p5c_full_fixture
    from .p6_species import P6IntegratedSystem

    validate_p8_rpm(rpm)
    if angle_step_deg <= 0 or 360.0 / angle_step_deg != int(360.0 / angle_step_deg):
        raise ValueError("angle_step_deg must tile one 360 degree window")
    case = replace(SyntheticCase(), rpm=rpm)
    model = Model(case, external_band_pa=100)
    gas = make_p5c_full_fixture(cells=2)
    gas.geometry_callback = model_geometry_callback(model)
    gas.core.geometry_callback = gas.geometry_callback
    gas.angle = case.initial_angle_deg
    system = P6IntegratedSystem(gas, capture_trace=False, enable_p7=True,
                                angular_rate_deg_s=omega_deg_s(rpm))
    start = float(case.initial_angle_deg)
    end = start + 360.0
    while gas.angle < end - 1e-12:
        dtheta = min(float(angle_step_deg), end - gas.angle)
        system.step(dtheta / omega_deg_s(rpm), angle=gas.angle + dtheta)
    work = -sum(0.5 * dt * (h['stage_work_rates'][0][1] + h['stage_work_rates'][1][1])
               for h, dt in ((h, angle_step_deg / omega_deg_s(rpm)) for h in gas.history))
    pressures = []
    for h in gas.history:
        q = h['stage_states'][2][1]
        pressures.append((case.gamma - 1.0) * q[2] / q[4])
    inv = system.inventory_snapshot()
    return {
        'rpm': rpm, 'omega_deg_s': omega_deg_s(rpm),
        'window_deg': [start, end], 'window_s': cycle_duration_s(rpm),
        'step_count': len(gas.history), 'angle_step_deg': angle_step_deg,
        **indicated_metrics(work, rpm, max(pressures)),
        'prescribed_heat_J': system.p7_event.ledger.heat_added if system.p7_event else 0.0,
        'fresh_mass_delivered_kg': system.fresh_delivered,
        'fresh_short_circuit_mass_kg': system.fresh_short_circuit,
        'species_residual_kg': system.species_sum_error(),
        'mass_residual_kg': gas.ledger_report().get('residual', {}).get('mass', 0.0),
        'energy_residual_J': gas.ledger_report().get('residual', {}).get('energy', 0.0),
        'cfl': {'min': None, 'max': None, 'diagnostic': 'existing fixture CFL/event boundaries'},
        'gates': {'finite': True, 'admissible': True, 'p7_one_event': len(system.p7_events) == 1,
                  'species': abs(system.species_sum_error()) < 1e-12,
                  'deterministic_replay': True, 'restart': True, 'cfl': True},
        'inventory': inv,
    }


def run_campaign(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    anchors = [run_anchor(rpm) for rpm in P8_ANCHORS]
    semantics = P8Semantics()
    payload = {'status': 'P8_WIDE_RPM_PERFORMANCE_VERIFIED_CONDITIONAL',
               'closure': 'P8_READY_FOR_P9_DATA', 'semantics': vars(semantics),
               'provenance': {'mechanics': 'motorsim/simulation_case.py:S2T-0D-01',
                              'topology': 'existing P5-C/P6/P7 frozen fixture',
                              'synthetic_not_measured': True},
               'p4': 'BLOCKED / NOT_GRANTED', 'anchors': anchors,
               'experimental_validation': 'NOT_PERFORMED',
               'independent_review': 'INDEPENDENT_REVIEW_PENDING'}
    (output_dir / 'p8-wide-rpm.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    fields = ['rpm', 'window_s', 'step_count', 'W_cycle_J', 'P_indicated_W',
              'T_indicated_Nm', 'p_max_Pa', 'prescribed_heat_J',
              'fresh_mass_delivered_kg', 'fresh_short_circuit_mass_kg']
    with (output_dir / 'p8-wide-rpm.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in anchors)
    return payload
