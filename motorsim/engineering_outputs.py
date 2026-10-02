"""Stable JSON-ready schema for available 2T engineering outputs."""
from __future__ import annotations

import math
from typing import Any

SCHEMA = "MOTORSIM_ENGINEERING_OUTPUTS_V1"
DEPENDENCIES = {"INDEPENDENT_OF_P4", "CONDITIONAL_ON_P4", "REVALIDATED_ON_P4_PASS"}
CHANNEL_UNITS = {
    "cylinder_pressure_pa": "Pa", "crankcase_pressure_pa": "Pa",
    "cylinder_temperature_k": "K", "crankcase_temperature_k": "K",
    "cylinder_mass_kg": "kg", "fresh_air_mass_kg": "kg", "fuel_mass_kg": "kg",
    "residual_mass_kg": "kg", "burned_mass_kg": "kg",
    "cylinder_volume_m3": "m^3", "crankcase_volume_m3": "m^3",
    "intake_port_area_m2": "m^2", "transfer_port_area_m2": "m^2",
    "exhaust_port_area_m2": "m^2", "intake_mass_flow_kg_s": "kg/s",
    "transfer_mass_flow_kg_s": "kg/s", "exhaust_mass_flow_kg_s": "kg/s",
    "intake_pressure_pa": "Pa", "transfer_pressure_pa": "Pa",
    "exhaust_pressure_pa": "Pa", "intake_mach": "1", "transfer_mach": "1",
    "exhaust_mach": "1", "combustion_fraction": "1",
    "heat_release_w": "W", "wall_heat_transfer_w": "W",
    "duct_temperature_k": "K", "duct_pressure_pa": "Pa",
    "duct_mass_flow_kg_s": "kg/s", "duct_mach": "1",
}
METRIC_UNITS = {
    "indicated_work_j": "J", "gross_work_j": "J", "net_work_j": "J",
    "indicated_power_w": "W", "brake_power_w": "W",
    "indicated_torque_nm": "N*m", "brake_torque_nm": "N*m",
    "imep_pa": "Pa", "bmep_pa": "Pa", "fmep_pa": "Pa",
    "delivery_ratio": "1", "trapping_efficiency": "1",
    "scavenging_efficiency": "1", "charging_efficiency": "1",
    "trapping_ratio": "1", "residual_fraction": "1",
    "short_circuit_fraction": "1", "fresh_delivery_kg": "kg",
    "fresh_short_circuit_kg": "kg", "peak_pressure_pa": "Pa",
    "angle_of_peak_pressure_deg": "degCA", "afr": "1",
    "equivalence_ratio": "1", "fuel_flow_kg_s": "kg/s",
    "isfc_g_kwh": "g/kWh", "bsfc_g_kwh": "g/kWh",
    "wall_heat_loss_j": "J", "energy_balance_residual_j": "J",
    "ca10_deg": "degCA", "ca50_deg": "degCA", "ca90_deg": "degCA",
}


def _finite(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite numeric data, excluding booleans")
    return float(value)


def build_engineering_output(*, rpm: float, cycle_number: int,
                             angles_deg: tuple[float, ...],
                             channels: dict[str, dict[str, Any]],
                             cycle_metrics: dict[str, dict[str, Any]],
                             dependency_status: str,
                             cycle_period_deg: float = 360.0) -> dict[str, Any]:
    speed = _finite(rpm, "rpm")
    period = _finite(cycle_period_deg, "cycle_period_deg")
    if speed <= 0 or period != 360.0:
        raise ValueError("This output contract requires positive RPM and a 360-degree 2T cycle")
    if type(cycle_number) is not int or cycle_number < 1:
        raise ValueError("cycle_number must be a positive integer")
    if dependency_status not in DEPENDENCIES:
        raise ValueError("dependency_status must be explicit")
    if not isinstance(angles_deg, tuple) or len(angles_deg) < 2:
        raise ValueError("A crank-angle trace requires at least two samples")
    angles = tuple(_finite(value, "angle_deg") for value in angles_deg)
    if any(right <= left for left, right in zip(angles, angles[1:])):
        raise ValueError("Crank-angle samples must increase strictly")
    if not math.isclose(angles[-1] - angles[0], period, rel_tol=0, abs_tol=16*math.ulp(period)):
        raise ValueError("Crank-angle trace must span one complete 2T cycle")
    if not isinstance(channels, dict) or not isinstance(cycle_metrics, dict):
        raise ValueError("Channels and cycle metrics must be mappings")

    trace = {}
    for name, record in channels.items():
        if name not in CHANNEL_UNITS or not isinstance(record, dict) or set(record) != {"values", "source"}:
            raise ValueError(f"Unsupported or malformed crank-angle channel: {name}")
        values = record["values"]
        if not isinstance(values, (tuple, list)) or len(values) != len(angles):
            raise ValueError(f"Channel {name} sample count does not match angle trace")
        source = record["source"]
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Channel {name} requires source provenance")
        trace[name] = {"unit": CHANNEL_UNITS[name], "source": source,
                       "values": [_finite(value, name) for value in values]}

    metrics = {}
    for name, record in cycle_metrics.items():
        if name not in METRIC_UNITS or not isinstance(record, dict) or set(record) != {
                "value", "status", "reason", "source"}:
            raise ValueError(f"Unsupported or malformed cycle metric: {name}")
        status, value, reason, source = (record[key] for key in ("status", "value", "reason", "source"))
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Metric {name} requires source provenance")
        if status == "DEFINED":
            value = _finite(value, name)
            if reason is not None:
                raise ValueError(f"Defined metric {name} cannot have an undefined reason")
        elif status == "UNDEFINED":
            if value is not None or not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"Undefined metric {name} requires null value and reason")
        else:
            raise ValueError(f"Metric {name} status must be DEFINED or UNDEFINED")
        metrics[name] = {"value": value, "unit": METRIC_UNITS[name],
                         "status": status, "reason": reason, "source": source}

    output = {"schema": SCHEMA,
              "operating_point": {"cycle_convention": "2T_360_DEG_ONE_CYCLE_PER_REV",
                                  "rpm": speed, "cycle_number": cycle_number,
                                  "dependency_status": dependency_status},
              "crank_angle_trace": {"angle_deg": list(angles), "channels": trace},
              "cycle_metrics": metrics,
              "claims": {"periodicity": "NOT_EVALUATED",
                         "experimental_validation": "NOT_PERFORMED",
                         "predictive_validation": "NOT_CLAIMED"}}
    return output


def validate_engineering_output(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("Engineering output schema is invalid")
    op = value.get("operating_point")
    trace = value.get("crank_angle_trace")
    if (not isinstance(op, dict) or set(op) != {"cycle_convention", "rpm", "cycle_number",
                                                "dependency_status"}
            or op["cycle_convention"] != "2T_360_DEG_ONE_CYCLE_PER_REV"
            or not isinstance(trace, dict) or set(trace) != {"angle_deg", "channels"}
            or not isinstance(trace["channels"], dict)):
        raise ValueError("Engineering output sections are missing")
    claims = value.get("claims")
    if claims != {"periodicity": "NOT_EVALUATED",
                  "experimental_validation": "NOT_PERFORMED",
                  "predictive_validation": "NOT_CLAIMED"}:
        raise ValueError("Engineering output claim controls were altered")
    metrics = value.get("cycle_metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Engineering output metrics are malformed")
    for name, row in trace["channels"].items():
        if not isinstance(row, dict) or row.get("unit") != CHANNEL_UNITS.get(name):
            raise ValueError(f"Channel {name} unit does not match schema")
    for name, row in metrics.items():
        if not isinstance(row, dict) or row.get("unit") != METRIC_UNITS.get(name):
            raise ValueError(f"Metric {name} unit does not match schema")
    return build_engineering_output(
        rpm=op.get("rpm"), cycle_number=op.get("cycle_number"),
        angles_deg=tuple(trace.get("angle_deg", ())), channels={
            name: {"values": row.get("values"), "source": row.get("source")}
            for name, row in trace.get("channels", {}).items()},
        cycle_metrics={name: {key: row.get(key) for key in
                              ("value", "status", "reason", "source")}
                       for name, row in metrics.items()},
        dependency_status=op.get("dependency_status"),
        cycle_period_deg=360.0)
