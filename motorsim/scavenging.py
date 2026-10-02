"""Scavenging diagnostics derived from P6 four-species masses and ledgers.

No transport or thermodynamic state is changed here. A zero ratio denominator
is represented explicitly as undefined rather than as a fabricated zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isfinite, pi
from typing import Any

SPECIES = ("fresh_air", "fuel", "residual", "burned")


def _number(value: Any, label: str, *, nonnegative=True) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{label}: se requiere número, sin booleanos ni texto.")
    try:
        finite = isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{label}: debe ser finito.")
    result = float(value)
    if nonnegative and result < 0.0:
        raise ValueError(f"{label}: no puede ser negativo.")
    if not isfinite(result):
        raise ValueError(f"{label}: fuera de rango.")
    return result


def reference_charge_mass(bore_mm: float, stroke_mm: float,
                          ambient_pressure_pa: float,
                          ambient_temperature_k: float,
                          gas_constant_j_kgk: float = 287.0) -> float:
    """Ambient fresh-air mass in swept volume for one cylinder, in kg."""
    bore = _number(bore_mm, "bore_mm") * 1e-3
    stroke = _number(stroke_mm, "stroke_mm") * 1e-3
    pressure = _number(ambient_pressure_pa, "ambient_pressure_pa")
    temperature = _number(ambient_temperature_k, "ambient_temperature_k")
    gas_constant = _number(gas_constant_j_kgk, "gas_constant_j_kgk")
    if min(bore, stroke, pressure, temperature, gas_constant) <= 0.0:
        raise ValueError("La geometría y el estado ambiente deben ser positivos.")
    volume = pi * bore * bore * stroke / 4.0
    result = pressure * volume / (gas_constant * temperature)
    return _number(result, "reference_charge_mass_kg")


def _species_mass(value: Any, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ValueError(f"{label}: se requieren cuatro masas P6 en orden {SPECIES}.")
    result = tuple(_number(item, f"{label}.{name}")
                   for name, item in zip(SPECIES, value))
    try:
        total = fsum(result)
    except OverflowError as exc:
        raise ValueError(f"{label}: masa total fuera de rango.") from exc
    if not isfinite(total):
        raise ValueError(f"{label}: masa total fuera de rango.")
    return result


@dataclass(frozen=True)
class RatioResult:
    value: float | None
    status: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "status": self.status, "reason": self.reason}


def _ratio(numerator: float, denominator: float) -> RatioResult:
    if denominator == 0.0:
        return RatioResult(None, "UNDEFINED", "ZERO_DENOMINATOR")
    value = numerator / denominator
    if not isfinite(value):
        raise ValueError("El cociente calculado está fuera de rango numérico.")
    return RatioResult(value, "AVAILABLE")


@dataclass(frozen=True)
class ScavengingInput:
    reference_mass_kg: float
    fresh_delivered_kg: float
    fresh_short_circuit_kg: float
    species_at_transfer_close_kg: tuple[float, float, float, float]
    species_at_exhaust_close_kg: tuple[float, float, float, float]


def calculate_scavenging_metrics(inputs: ScavengingInput) -> dict[str, Any]:
    """Calculate cycle metrics from authoritative masses and P6 ledgers.

    `species_at_transfer_close_kg` is sampled after the last transfer closes;
    `species_at_exhaust_close_kg` is sampled after the last exhaust aperture
    closes. `fresh_short_circuit_kg` must be the P6 outward exhaust ledger.
    This function never infers a lost mass from a reverse exhaust flow.
    """
    reference = _number(inputs.reference_mass_kg, "reference_mass_kg")
    delivered = _number(inputs.fresh_delivered_kg, "fresh_delivered_kg")
    lost = _number(inputs.fresh_short_circuit_kg, "fresh_short_circuit_kg")
    transfer = _species_mass(inputs.species_at_transfer_close_kg,
                             "species_at_transfer_close_kg")
    exhaust = _species_mass(inputs.species_at_exhaust_close_kg,
                            "species_at_exhaust_close_kg")
    transfer_total = fsum(transfer)
    exhaust_total = fsum(exhaust)
    transfer_fresh = fsum(transfer[:2])
    exhaust_fresh = fsum(exhaust[:2])
    retained = exhaust_fresh

    metrics = {
        "delivery_ratio": _ratio(delivered, reference),
        "trapping_efficiency": _ratio(retained, delivered),
        "scavenging_efficiency": _ratio(retained, exhaust_total),
        "charging_efficiency": _ratio(retained, reference),
        "trapping_ratio": _ratio(delivered, retained),
        "residual_fraction": _ratio(exhaust[2], exhaust_total),
        "purity_at_transfer_close": _ratio(transfer_fresh, transfer_total),
        "purity_at_exhaust_close": _ratio(exhaust_fresh, exhaust_total),
        "short_circuit_fraction": _ratio(lost, delivered),
    }
    return {
        "schema": "MOTORSIM_2T_SCAVENGING_METRICS_V1",
        "basis": "P6 four-species inventories and outward-flow ledgers",
        "species_order": list(SPECIES),
        "masses_kg": {"reference": reference, "fresh_delivered": delivered,
                      "fresh_retained": retained, "fresh_lost": lost,
                      "transfer_close_total": transfer_total,
                      "exhaust_close_total": exhaust_total,
                      "transfer_close_fresh": transfer_fresh,
                      "exhaust_close_fresh": exhaust_fresh,
                      "exhaust_close_residual": exhaust[2]},
        "ratios": {name: value.to_dict() for name, value in metrics.items()},
        "formulae": {
            "delivery_ratio": "fresh_delivered / reference_mass",
            "trapping_efficiency": "fresh_retained / fresh_delivered",
            "scavenging_efficiency": "fresh_retained / exhaust_close_total",
            "charging_efficiency": "fresh_retained / reference_mass",
            "trapping_ratio": "fresh_delivered / fresh_retained",
            "residual_fraction": "exhaust_close_residual / exhaust_close_total",
            "purity_at_transfer_close": "transfer_close_fresh / transfer_close_total",
            "purity_at_exhaust_close": "exhaust_close_fresh / exhaust_close_total",
            "short_circuit_fraction": "fresh_lost / fresh_delivered",
        },
    }
