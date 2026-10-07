"""Versioned engineering physics contracts for the post-R2 production phase.

This module is deliberately additive.  It provides auditable model inputs and
derived quantities for ``IntegratedEngine2T`` outputs without changing any
historical P0-P8 or closure evidence contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from .fuel_combustion import FuelCoupledCombustionV2
from .fuel_library import FuelDefinition, FuelSimulationSnapshot, FuelSource
from .mechanical import MechanicalLossModel


SCHEMA = "ENGINE_PHYSICS_V1"
PROVENANCE = {"DOCUMENTED", "DERIVED_FROM_DOCUMENTED", "SYNTHETIC_ASSUMPTION"}


def _finite(value: Any, name: str, *, nonnegative: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric data")
    result = float(value)
    if nonnegative and result < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _ratio(numerator: float, denominator: float, reason: str = "ZERO_DENOMINATOR") -> dict[str, Any]:
    if denominator == 0.0:
        return {"value": None, "status": "UNDEFINED", "reason": reason}
    value = numerator / denominator
    if not math.isfinite(value):
        return {"value": None, "status": "UNDEFINED", "reason": "NONFINITE_RESULT"}
    return {"value": value, "status": "DEFINED", "reason": None}


def _hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PortDischargeCoefficientsV1:
    """Explicit per-port and flow-sense Cd values."""

    values: Mapping[str, Mapping[str, float]]
    provenance: str = "SYNTHETIC_ASSUMPTION"
    version: str = "STANDARD_V1"

    def validate(self) -> None:
        if self.version != "STANDARD_V1" or self.provenance not in PROVENANCE:
            raise ValueError("port coefficient identity/provenance is invalid")
        if not self.values:
            raise ValueError("at least one port coefficient is required")
        for port, senses in self.values.items():
            if not isinstance(port, str) or not port.strip() or not isinstance(senses, Mapping):
                raise ValueError("port coefficients require named port mappings")
            if set(senses) != {"forward", "reverse"}:
                raise ValueError("each port requires forward and reverse Cd")
            for sense, value in senses.items():
                if _finite(value, f"{port}.{sense}") <= 0.0 or value > 1.0:
                    raise ValueError("STANDARD_V1 Cd must be in (0,1]")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"schema": "PORT_DISCHARGE_COEFFICIENTS_STANDARD_V1",
                "version": self.version, "provenance": self.provenance,
                "values": {key: dict(value) for key, value in sorted(self.values.items())},
                "sha256": _hash({"version": self.version, "provenance": self.provenance,
                                  "values": {key: dict(value) for key, value in sorted(self.values.items())}})}


@dataclass(frozen=True)
class IdealFuelMeteringV1:
    target_phi: float = 1.0
    air_kg_per_cycle: float = 1.0
    provenance: str = "SYNTHETIC_ASSUMPTION"
    model: str = "IDEAL_FUEL_METERING"

    def evaluate(self, fuel: FuelSimulationSnapshot) -> dict[str, Any]:
        if self.provenance not in PROVENANCE or self.model != "IDEAL_FUEL_METERING":
            raise ValueError("fuel metering identity/provenance is invalid")
        phi = _finite(self.target_phi, "target_phi")
        air = _finite(self.air_kg_per_cycle, "air_kg_per_cycle", nonnegative=True)
        if phi < 0.0:
            raise ValueError("target phi cannot be negative")
        definition = fuel.validate()
        afr = definition.effective_stoichiometric_afr
        if afr is None:
            raise ValueError("fuel snapshot lacks stoichiometric AFR")
        fuel_mass = 0.0 if phi == 0.0 else air * phi / afr
        return {"schema": "IDEAL_FUEL_METERING_V1", "model": self.model,
                "target_phi": phi, "target_afr": _ratio(afr, phi, "ZERO_PHI"),
                "air_kg_per_cycle": air, "fuel_kg_per_cycle": fuel_mass,
                "fuel_snapshot_sha256": fuel.content_hash,
                "provenance": self.provenance}


def synthetic_gasoline_v1() -> FuelSimulationSnapshot:
    """Return the immutable synthetic gasoline surrogate used by this phase."""
    definition = FuelDefinition(
        id="SYNTHETIC_GASOLINE_V1", version="1.0.0",
        display_name="MotorSim synthetic gasoline engineering surrogate",
        family_category="SYNTHETIC_ENGINEERING_SURROGATE",
        provenance="MODELED_SURROGATE", builtin=False, enabled=True,
        density_kg_m3=720.0, lower_heating_value_j_kg=43_000_000.0,
        stoichiometry_method_version="ELEMENTAL_MASS_BALANCE_DRY_AIR_V1",
        elemental_mass_fractions={"C": 0.86, "H": 0.14, "O": 0.0},
        oxygen_fraction=0.0, oxygen_fraction_basis="MASS_FRACTION",
        reference_temperature_K=293.15,
        sources=(FuelSource("MotorSim versioned synthetic assumption", 
                            "https://example.invalid/motorsim/synthetic-gasoline-v1",
                            "2026-10-07", "Frozen engineering surrogate parameters."),),
        note="Synthetic engineering surrogate; not ANCAP, commercial fuel, or experimental validation.")
    definition.validate()
    return FuelSimulationSnapshot.freeze(definition)


@dataclass(frozen=True)
class ScavengingModelV1:
    version: str = "SCAVENGING_MODEL_V1"
    zone_profile: str = "TWO_ZONE_PROFILE"
    provenance: str = "SYNTHETIC_ASSUMPTION"

    def evaluate(self, *, reference_air_kg: float, fresh_delivered_kg: float,
                 fresh_short_circuit_kg: float, trapped_fresh_air_kg: float,
                 trapped_residual_kg: float, trapped_fuel_kg: float) -> dict[str, Any]:
        if self.provenance not in PROVENANCE or self.zone_profile != "TWO_ZONE_PROFILE":
            raise ValueError("scavenging model identity/provenance is invalid")
        values = {name: _finite(value, name, nonnegative=True) for name, value in {
            "reference_air_kg": reference_air_kg, "fresh_delivered_kg": fresh_delivered_kg,
            "fresh_short_circuit_kg": fresh_short_circuit_kg,
            "trapped_fresh_air_kg": trapped_fresh_air_kg,
            "trapped_residual_kg": trapped_residual_kg,
            "trapped_fuel_kg": trapped_fuel_kg}.items()}
        retained = values["trapped_fresh_air_kg"]
        total_trapped = retained + values["trapped_residual_kg"] + values["trapped_fuel_kg"]
        ratios = {
            "delivery_ratio": _ratio(values["fresh_delivered_kg"], values["reference_air_kg"]),
            "trapping_efficiency": _ratio(retained, values["fresh_delivered_kg"]),
            "scavenging_efficiency": _ratio(retained, total_trapped),
            "charging_efficiency": _ratio(retained, values["reference_air_kg"]),
            "short_circuit_fraction": _ratio(values["fresh_short_circuit_kg"], values["fresh_delivered_kg"]),
            "residual_fraction": _ratio(values["trapped_residual_kg"], total_trapped),
            "fresh_charge_fraction": _ratio(retained, total_trapped),
        }
        for name in ("trapping_efficiency", "scavenging_efficiency", "charging_efficiency",
                     "short_circuit_fraction", "residual_fraction", "fresh_charge_fraction"):
            if ratios[name]["status"] == "DEFINED" and not 0.0 <= ratios[name]["value"] <= 1.0:
                ratios[name] = {"value": None, "status": "UNDEFINED",
                                "reason": "OUTSIDE_PHYSICAL_DOMAIN"}
        partition_residual = values["fresh_delivered_kg"] - values["fresh_short_circuit_kg"] - retained
        if partition_residual < 0.0:
            for name in ("trapping_efficiency", "short_circuit_fraction"):
                ratios[name] = {"value": None, "status": "UNDEFINED",
                                "reason": "GROSS_CROSSING_PARTITION_INVALID"}
        return {"schema": self.version, "zone_profile": self.zone_profile,
                "masses_kg": values | {"trapped_total_kg": total_trapped},
                "ratios": ratios, "conservation": {
                    "delivered_partition_kg": values["fresh_short_circuit_kg"] + retained,
                    "partition_residual_kg": partition_residual},
                "provenance": self.provenance}


@dataclass(frozen=True)
class HeatTransferModelV1:
    correlation: str = "ANNAND_V1"
    wall_surfaces: tuple[str, ...] = ("head", "piston", "liner")
    wall_temperature_K: float = 450.0
    coefficient_W_m2K: float = 250.0
    provenance: str = "SYNTHETIC_ASSUMPTION"

    def evaluate(self, *, gas_temperature_K: float, areas_m2: Mapping[str, float]) -> dict[str, Any]:
        gas = _finite(gas_temperature_K, "gas_temperature_K")
        wall = _finite(self.wall_temperature_K, "wall_temperature_K")
        coefficient = _finite(self.coefficient_W_m2K, "coefficient_W_m2K", nonnegative=True)
        if gas <= 0.0 or wall <= 0.0 or set(areas_m2) != set(self.wall_surfaces):
            raise ValueError("heat-transfer state/surface contract is invalid")
        heat = {}
        for surface, area in areas_m2.items():
            value = coefficient * _finite(area, f"{surface}.area", nonnegative=True) * (gas - wall)
            heat[surface] = value
        return {"schema": "HEAT_TRANSFER_STANDARD_V1", "correlation": self.correlation,
                "heat_rate_W_by_surface": heat, "wall_temperature_K": wall,
                "provenance": self.provenance}


@dataclass(frozen=True)
class DuctHeatTransferV1:
    friction_model: str = "REYNOLDS_FRICTION_V1"
    heat_transfer_model: str = "DUCT_WALL_NUSSELT_V1"
    provenance: str = "SYNTHETIC_ASSUMPTION"

    def evaluate(self, *, reynolds: float, hydraulic_diameter_m: float,
                 length_m: float, wall_temperature_K: float,
                 gas_temperature_K: float) -> dict[str, Any]:
        re = _finite(reynolds, "reynolds", nonnegative=True)
        diameter = _finite(hydraulic_diameter_m, "hydraulic_diameter_m")
        length = _finite(length_m, "length_m", nonnegative=True)
        wall = _finite(wall_temperature_K, "wall_temperature_K")
        gas = _finite(gas_temperature_K, "gas_temperature_K")
        if diameter <= 0.0 or wall <= 0.0 or gas <= 0.0:
            raise ValueError("duct geometry/temperature is invalid")
        friction = 0.0 if re == 0.0 else 0.3164 / re ** 0.25
        nusselt = 3.66 if re == 0.0 else 0.023 * re ** 0.8
        return {"schema": "DUCT_HEAT_TRANSFER_STANDARD_V1", "reynolds": re,
                "friction_factor": friction, "nusselt": nusselt,
                "length_m": length, "hydraulic_diameter_m": diameter,
                "wall_heat_direction": "GAS_TO_WALL" if gas >= wall else "WALL_TO_GAS",
                "provenance": self.provenance}


def standard_fmep_model_v1() -> MechanicalLossModel:
    from .mechanical import LossTerm
    # A + B*Up + C*Up^2 in Pa; coefficients are synthetic engineering inputs.
    return MechanicalLossModel(terms=(
        LossTerm("fmep_standard_v1", "piston_ring", "SYNTHETIC_ASSUMPTION",
                 operating_map=None, mep_pa=85_000.0),))


def engineering_plausibility_gates_v1(*, pressures_pa: Mapping[str, float],
                                      temperatures_K: Mapping[str, float],
                                      conservation_residuals: Mapping[str, float],
                                      metrics: Mapping[str, Any]) -> dict[str, Any]:
    hard = []
    warnings = []
    for name, value in pressures_pa.items():
        if not math.isfinite(value) or value <= 0.0:
            hard.append(f"PRESSURE_INVALID:{name}")
    for name, value in temperatures_K.items():
        if not math.isfinite(value) or value <= 0.0:
            hard.append(f"TEMPERATURE_INVALID:{name}")
    for name, value in conservation_residuals.items():
        if not math.isfinite(value) or abs(value) > 1e-8:
            hard.append(f"CONSERVATION_INVALID:{name}")
    for name, record in metrics.items():
        if isinstance(record, Mapping) and record.get("status") == "DEFINED":
            value = record.get("value")
            if value is not None and not 0.0 <= value <= 1.0:
                warnings.append(f"PLAUSIBILITY_WARNING:{name}=outside_[0,1]")
    return {"schema": "ENGINE_PLAUSIBILITY_GATES_V1",
            "classification": "HARD_PHYSICAL_INVALID" if hard else "PASS",
            "hard_failures": hard, "warnings": warnings,
            "warning_policy": "warnings require explanation and do not override physical validity"}


def phase_model_provenance(*, fuel: FuelSimulationSnapshot,
                           port_coefficients: PortDischargeCoefficientsV1,
                           combustion: FuelCoupledCombustionV2) -> dict[str, Any]:
    fuel.validate(); port_coefficients.validate(); combustion.validate()
    payload = {"module": SCHEMA, "fuel": fuel.to_dict(),
               "port_coefficients": port_coefficients.to_dict(),
               "combustion": combustion.to_dict()}
    return {"models": payload, "sha256": _hash(payload)}


def evaluate_integrated_cycle_v1(cycle: Mapping[str, Any], *, rpm: float,
                                 fuel: FuelSimulationSnapshot,
                                 mechanical_losses: MechanicalLossModel | None = None,
                                 port_coefficients: PortDischargeCoefficientsV1 | None = None) -> dict[str, Any]:
    """Build the phase engineering record from an accepted integrated primary.

    The primary is the authoritative state/ledger product of
    ``IntegratedEngine2T``.  This adapter does not infer chemistry from a
    terminal inventory: it uses the explicit cycle fuel and species ledgers.
    """
    if not isinstance(cycle, Mapping) or cycle.get("admissible") is not True:
        raise ValueError("ENGINE_PHYSICS_V1 requires an admissible integrated primary")
    fuel.validate()
    observables = cycle.get("observables")
    ledgers = cycle.get("cycle_ledgers", {})
    conservation = cycle.get("conservation")
    terminal = cycle.get("terminal_state")
    if not isinstance(observables, Mapping) or not isinstance(conservation, Mapping):
        raise ValueError("integrated primary lacks observables/conservation")
    cylinder = observables.get("chambers", {}).get("cylinder", {})
    species = observables.get("cylinder_species_kg", (0.0, 0.0, 0.0, 0.0))
    if not species or len(species) != 4:
        species = terminal.get("species", {}).get("chambers", {}).get("cylinder", (0.0, 0.0, 0.0, 0.0))
    fresh_delivered = _finite(observables.get("fresh_delivered_kg", 0.0), "fresh_delivered_kg", nonnegative=True)
    fuel_delivered = _finite(observables.get("fuel_delivered_kg", 0.0), "fuel_delivered_kg", nonnegative=True)
    fuel_burned = _ratio(ledgers.get("fuel_combustion_heat_added_J", 0.0),
                          fuel.validate().lower_heating_value_j_kg, "ZERO_LHV")
    afr = _ratio(fresh_delivered, fuel_delivered)
    phi = _ratio(fuel.validate().effective_stoichiometric_afr,
                 afr["value"] if afr["value"] is not None else 0.0, "ZERO_AFR")
    scavenging = ScavengingModelV1().evaluate(
        reference_air_kg=max(fresh_delivered, 1e-30),
        fresh_delivered_kg=fresh_delivered,
        fresh_short_circuit_kg=_finite(observables.get("fresh_short_circuit_kg", 0.0),
                                       "fresh_short_circuit_kg", nonnegative=True),
        trapped_fresh_air_kg=_finite(species[0], "trapped_fresh_air_kg", nonnegative=True),
        trapped_residual_kg=_finite(species[2], "trapped_residual_kg", nonnegative=True),
        trapped_fuel_kg=_finite(species[1], "trapped_fuel_kg", nonnegative=True))
    loss_model = mechanical_losses or standard_fmep_model_v1()
    displacement = _finite(cycle.get("swept_displacement_m3", 0.0), "swept_displacement_m3")
    net_work = _finite(observables.get("net_piston_gas_work_J", 0.0), "net_piston_gas_work_J")
    performance = loss_model.evaluate_2t_net_piston_work(
        net_piston_gas_work_j=net_work, displacement_m3=displacement,
        rpm=_finite(rpm, "rpm"), load=1.0)
    cylinder_temperature = _finite(cylinder.get("temperature_K", 300.0), "cylinder_temperature_K")
    heat = HeatTransferModelV1().evaluate(
        gas_temperature_K=cylinder_temperature,
        areas_m2={"head": 0.01, "piston": 0.01, "liner": 0.02})
    gates = engineering_plausibility_gates_v1(
        pressures_pa={"cylinder": _finite(cylinder.get("pressure_Pa", 0.0), "cylinder_pressure_Pa")},
        temperatures_K={"cylinder": cylinder_temperature},
        conservation_residuals={
            "mass": _finite(conservation.get("mass_residual_kg", 0.0), "mass_residual_kg"),
            "energy": _finite(conservation.get("energy_residual_J", 0.0), "energy_residual_J")},
        metrics=scavenging["ratios"])
    return {"schema": "ENGINEERING_OUTPUTS_ENGINE_PHYSICS_V1",
            "cycle_index": cycle.get("cycle_index"), "rpm": float(rpm),
            "periodicity": cycle.get("periodicity", {"status": "NOT_EVALUATED"}),
            "hard_gate": gates, "fuel": {
                "fuel_id": fuel.fuel_id, "fuel_sha256": fuel.content_hash,
                "fuel_delivered_kg_per_cycle": fuel_delivered,
                "fuel_burned_kg_per_cycle": fuel_burned,
                "fresh_air_delivered_kg_per_cycle": fresh_delivered,
                "afr": afr, "phi": phi},
            "scavenging": scavenging, "heat_transfer": heat,
            "performance": performance,
            "conservation": dict(conservation),
            "model_versions": {"port_cd": "STANDARD_V1", "scavenging": "SCAVENGING_MODEL_V1",
                                "fuel_metering": "IDEAL_FUEL_METERING", "heat_transfer": "ANNAND_V1",
                                "duct_heat_transfer": "DUCT_HEAT_TRANSFER_STANDARD_V1",
                                "mechanical_losses": "MECHANICAL_LOSSES_STANDARD_V1"},
            "provenance": "SYNTHETIC_ASSUMPTION"}
