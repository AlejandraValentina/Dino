"""Generic, stage-coherent 2T finite-volume engine integration.

This is an orchestration layer over the existing Euler EOS, mesh, HLLC and
0D/1D Riemann interface.  It does not alter the historical P5/P6 campaign
implementations or add another numerical flux law.  Four species are stored
as extensive masses and are authoritative; the legacy passive scalar in the
Euler vector is regenerated as total mass density.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json
from math import fsum, isclose, isfinite, pi
from types import MappingProxyType
from collections.abc import Mapping
from typing import Callable
from urllib.parse import quote

from .crankcase import CrankcaseGeometry
from .coupling import ChamberState, interface_flux
from .gas1d.boundary import Boundary
from .gas1d.eos import IdealGas
from .gas1d.mesh import Mesh
from .gas1d.riemann import hllc_flux
from .kinematics import piston_position
from .network_components import (NetworkConnection, VolumeGasState, VolumeNode,
                                 VOLUME_KINDS, resolve_volume_duct_interface)
from .p6_species import (SPECIES, atmospheric_species, donor_species,
                         legacy_to_species, validate_species)
from .p7_prescribed import (P7BurnEvent, P7Ledger, Q_F, capture_event,
                            restore_event, snapshot_event)
from .powervalve import PowerValve
from .reed import ReedPetal, static_area
from .thermal import ThermalSystem
from .two_stroke_ports import TwoStrokePortSet

_USE_ACTIVE_P7_EVENT = object()


def _restore_validated_p7_event(value):
    event_fields = {"start", "fresh_air", "fuel", "ledger"}
    ledger_fields = set(vars(P7Ledger()))
    if (not isinstance(value, dict) or set(value) != event_fields or
            any(type(value[name]) not in (int, float) or
                not isfinite(value[name]) or value[name] < 0.0
                for name in ("start", "fresh_air", "fuel")) or
            not isinstance(value["ledger"], dict) or
            set(value["ledger"]) != ledger_fields):
        raise ValueError("integrated engine checkpoint P7 event is invalid")
    if any(type(number) not in (int, float) or not isfinite(number)
           for number in value["ledger"].values()):
        raise ValueError("integrated engine checkpoint P7 ledger is invalid")
    event = restore_event(value)
    ledger = event.ledger
    tolerance = 1e-12
    if (ledger.fresh_air_converted < -tolerance or
            ledger.fuel_converted < -tolerance or
            ledger.burned_produced < -tolerance or
            ledger.heat_added < -tolerance or
            ledger.fresh_air_converted > event.fresh_air + tolerance or
            ledger.fuel_converted > event.fuel + tolerance or
            ledger.burned_produced > event.fresh + tolerance or
            not abs(ledger.fresh_air_converted + ledger.fuel_converted -
                    ledger.burned_produced) <= tolerance or
            not abs(ledger.source_mass_residual) <= tolerance or
            not abs(ledger.residual_unchanged) <= tolerance or
            not abs(ledger.heat_burn_residual) <= tolerance or
            not isclose(ledger.heat_added, Q_F * ledger.burned_produced,
                        rel_tol=1e-12, abs_tol=1e-12)):
        raise ValueError("integrated engine checkpoint P7 ledger is inconsistent")
    return event


def _tuplify(value):
    if isinstance(value, list):
        return tuple(_tuplify(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuplify(item) for key, item in value.items()}
    return value


def _jsonify(value):
    """Return one stable JSON-shaped representation for replay evidence."""
    if isinstance(value, (list, tuple)):
        return [_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonify(item) for key, item in value.items()}
    return value


def _port_face_flux(exchange, duct_primitive, geometric_area, effective_area):
    """Return +x extensive flux, including pressure traction on blocked area.

    The Riemann exchange covers only the open portion of the duct face. The
    remaining geometric area is a stationary wall and carries the local duct
    pressure traction, but no mass, energy, or species exchange.
    """
    blocked_area = geometric_area - effective_area
    if blocked_area < -1e-15 * max(1.0, geometric_area):
        raise ValueError("effective port area exceeds the duct face")
    face = [0.0, 0.0, 0.0] if exchange is None else list(exchange.flux_x[:3])
    face[1] += max(0.0, blocked_area) * duct_primitive[2]
    return tuple(face)


def _gross_fresh_short_circuit_rate(exhaust_area, transfer_areas, species_flux):
    """Gross outward fresh species through an open exhaust/transfer path only."""
    if exhaust_area <= 0.0 or not any(area > 0.0 for area in transfer_areas):
        return 0.0
    return max(0.0, species_flux[0] + species_flux[1])


def _duct_ids_by_role(duct_roles: dict) -> dict[str, tuple[str, ...]]:
    """Resolve CONFIG_V2 output channels from role metadata, never literal ids."""
    if not isinstance(duct_roles, dict) or not duct_roles:
        raise ValueError("cycle primary record lacks stable duct role identity")
    grouped = {role: [] for role in ("intake", "transfer", "exhaust")}
    for duct_id, role in duct_roles.items():
        if (not isinstance(duct_id, str) or not duct_id or
                not isinstance(role, str) or role not in grouped):
            raise ValueError("cycle primary record contains an invalid duct role")
        grouped[role].append(duct_id)
    if (len(grouped["intake"]) != 1 or len(grouped["exhaust"]) != 1 or
            len(grouped["transfer"]) < 3):
        raise ValueError(
            "MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V2 supports one intake, "
            "at least three transfer paths and one exhaust")
    return {role: tuple(ids) for role, ids in grouped.items()}


def _role_face_outputs(face_fluxes: dict, role_ids: dict) -> dict[str, float]:
    intake = face_fluxes[role_ids["intake"][0]]
    exhaust = face_fluxes[role_ids["exhaust"][0]]
    return {
        "intake_port_area_m2": intake["effective_reed_area_m2"],
        "intake_mass_flow_kg_s": intake["right"][0],
        "transfer_mass_flow_kg_s": sum(
            face_fluxes[path]["right"][0] for path in role_ids["transfer"]),
        "exhaust_mass_flow_kg_s": exhaust["left"][0],
    }


@dataclass(frozen=True)
class EngineGeometry2T:
    """Resolved stage geometry in SI units, keyed by stable duct id."""
    crankcase_volume_m3: float
    cylinder_volume_m3: float
    crankcase_volume_rate_m3_s: float
    cylinder_volume_rate_m3_s: float
    intake_area_m2: float
    transfer_areas_m2: tuple[float, ...]
    exhaust_area_m2: float

    def validate(self, transfer_ids: tuple[str, ...]) -> None:
        values = (self.crankcase_volume_m3, self.cylinder_volume_m3,
                  self.crankcase_volume_rate_m3_s, self.cylinder_volume_rate_m3_s,
                  self.intake_area_m2, self.exhaust_area_m2, *self.transfer_areas_m2)
        if any(type(value) not in (int, float) or not isfinite(value) for value in values):
            raise ValueError("stage geometry must contain finite numeric values")
        if min(self.crankcase_volume_m3, self.cylinder_volume_m3) <= 0:
            raise ValueError("chamber volumes must be positive")
        if min(self.intake_area_m2, self.exhaust_area_m2, *self.transfer_areas_m2) < 0:
            raise ValueError("port areas cannot be negative")
        if len(self.transfer_areas_m2) != len(transfer_ids) or not transfer_ids:
            raise ValueError("geometry must resolve every configured transfer route")


@dataclass(frozen=True)
class SliderCrankChambers2T:
    """Resolve the existing crankcase model and matching 2T cylinder volume."""
    crankcase: CrankcaseGeometry
    cylinder_compression_ratio: float

    def validate(self) -> None:
        if not isinstance(self.crankcase, CrankcaseGeometry):
            raise ValueError("slider-crank chambers require existing CrankcaseGeometry")
        self.crankcase.validate()
        if (type(self.cylinder_compression_ratio) not in (int, float) or
                not isfinite(self.cylinder_compression_ratio) or
                self.cylinder_compression_ratio <= 1.0):
            raise ValueError("cylinder compression ratio must be finite and greater than one")

    def resolve(self, angle_deg: float, rpm: float) -> tuple[float, float, float, float]:
        self.validate()
        position = piston_position(self.crankcase.stroke_mm,
                                   self.crankcase.rod_length_mm, angle_deg)
        swept = self.crankcase.displacement_m3
        cylinder_clearance = swept / (self.cylinder_compression_ratio - 1.0)
        cylinder_volume = cylinder_clearance + swept * position / self.crankcase.stroke_mm
        crankcase_volume = self.crankcase.volume_m3(angle_deg)
        crankcase_rate = self.crankcase.volume_rate_m3_s(angle_deg, rpm)
        result = (crankcase_volume, cylinder_volume, crankcase_rate, -crankcase_rate)
        if any(not isfinite(value) for value in result) or min(result[:2]) <= 0.0:
            raise ValueError("slider-crank chamber geometry is inadmissible")
        return result

    def to_dict(self) -> dict:
        self.validate()
        return {"schema": "INTEGRATED_SLIDER_CRANK_CHAMBERS_2T_V1",
                "crankcase": self.crankcase.to_dict(),
                "cylinder_compression_ratio": self.cylinder_compression_ratio}


@dataclass(frozen=True)
class DuctPath2T:
    id: str
    mesh: object
    role: str

    def validate(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("duct path requires a stable id")
        if self.role not in {"intake", "transfer", "exhaust"}:
            raise ValueError("unsupported duct role")
        if not isinstance(self.mesh, Mesh):
            raise ValueError("duct path requires the existing immutable Mesh model")
        if any(not isinstance(getattr(self.mesh, name), tuple) for name in
               ("faces", "areas", "volumes", "centers")):
            raise ValueError("duct Mesh geometry must be immutable tuples")
        if not self.mesh.volumes or not self.mesh.areas:
            raise ValueError("duct path requires a populated finite-volume mesh")
        if len(self.mesh.areas) != len(self.mesh.volumes) + 1:
            raise ValueError("duct mesh face/cell shape mismatch")


@dataclass(frozen=True)
class IntegratedPortBinding2T:
    """Bind existing generic port ducts to the integrated finite-volume paths."""
    port_set: TwoStrokePortSet
    path_by_duct: dict[str, str]
    powervalve: PowerValve | None = None

    def __post_init__(self):
        if isinstance(self.path_by_duct, Mapping):
            object.__setattr__(self, "path_by_duct",
                               MappingProxyType(dict(self.path_by_duct)))

    def validate(self, paths: tuple[DuctPath2T, ...]) -> None:
        if not isinstance(self.port_set, TwoStrokePortSet):
            raise ValueError("port binding requires the existing TwoStrokePortSet")
        self.port_set.validate()
        if not isinstance(self.path_by_duct, Mapping) or set(self.path_by_duct) != {
                duct.id for duct in self.port_set.ducts}:
            raise ValueError("every generic port duct must map to one integrated path")
        path_roles = {path.id: path.role for path in paths}
        if any(path_id not in path_roles for path_id in self.path_by_duct.values()):
            raise ValueError("generic port binding names an unknown integrated path")
        duct_roles = {duct.id: duct.role for duct in self.port_set.ducts}
        for duct_id, path_id in self.path_by_duct.items():
            if duct_roles[duct_id] != path_roles[path_id]:
                raise ValueError(f"{duct_id}: generic and integrated path roles differ")
        if set(self.path_by_duct.values()) != path_roles.keys():
            raise ValueError("every integrated path requires an explicit generic port binding")
        if self.powervalve is not None:
            if not isinstance(self.powervalve, PowerValve):
                raise ValueError("powervalve must use the existing PowerValve model")
            self.powervalve.validate()
            target = next((port for port in self.port_set.ports
                           if port.id == self.powervalve.exhaust_port_id), None)
            if target is None or target.role != "exhaust":
                raise ValueError("powervalve target must be a bound exhaust port")

    def resolve(self, paths: tuple[DuctPath2T, ...], angle_deg: float,
                rpm: float) -> tuple[float, tuple[float, ...], float]:
        areas = {path.id: 0.0 for path in paths}
        for port in self.port_set.ports:
            if self.powervalve is not None and port.id == self.powervalve.exhaust_port_id:
                area_mm2 = self.powervalve.area_at(self.port_set, rpm, angle_deg)
            else:
                area_mm2 = self.port_set.area_at(port, angle_deg)
            path_id = self.path_by_duct[port.duct_id]
            areas[path_id] += area_mm2 * 1e-6
        intake = next(path for path in paths if path.role == "intake")
        exhaust = next(path for path in paths if path.role == "exhaust")
        transfers = tuple(path.id for path in paths if path.role == "transfer")
        return areas[intake.id], tuple(areas[path_id] for path_id in transfers), areas[exhaust.id]

    def to_dict(self) -> dict:
        return {"port_set": self.port_set.to_dict(),
                "path_by_duct": dict(self.path_by_duct),
                "powervalve": None if self.powervalve is None else self.powervalve.to_dict()}


@dataclass(frozen=True)
class IntegratedIntakePlenum2T:
    """One finite 0D plenum conservatively connected to the intake duct inlet."""
    node: VolumeNode
    connection: NetworkConnection
    initial_state: VolumeGasState

    def validate(self, intake: DuctPath2T) -> None:
        if not isinstance(self.node, VolumeNode) or not isinstance(self.connection, NetworkConnection):
            raise ValueError("intake plenum requires existing network node and connection models")
        self.node.validate()
        self.connection.validate()
        if self.node.kind != "plenum":
            raise ValueError("integrated intake volume must have kind plenum")
        if (self.connection.upstream != self.node.id or
                self.connection.downstream != intake.id or intake.role != "intake"):
            raise ValueError("intake plenum connection must terminate at the intake duct")
        if not isinstance(self.initial_state, VolumeGasState):
            raise ValueError("intake plenum requires an initial gas state")
        self.initial_state.validate()

    def to_dict(self) -> dict:
        self.node.validate()
        self.connection.validate()
        self.initial_state.validate()
        return {"schema": "INTEGRATED_INTAKE_PLENUM_2T_V1",
                "node": self.node.to_dict(), "connection": self.connection.to_dict(),
                "initial_state": {"mass_kg": self.initial_state.mass_kg,
                                  "internal_energy_j": self.initial_state.internal_energy_j,
                                  "species_mass_kg": list(self.initial_state.species_mass_kg)}}


@dataclass(frozen=True)
class IntegratedNetworkVolume2T:
    """Finite network volume bound to one external end of one gas duct."""
    node: VolumeNode
    connection: NetworkConnection
    duct_id: str
    side: str
    initial_state: VolumeGasState

    def validate(self, ducts: dict[str, DuctPath2T]) -> None:
        if (not isinstance(self.node, VolumeNode) or
                not isinstance(self.connection, NetworkConnection) or
                not isinstance(self.initial_state, VolumeGasState)):
            raise ValueError("integrated network binding uses invalid network components")
        self.node.validate()
        self.connection.validate()
        self.initial_state.validate()
        if not isinstance(self.duct_id, str) or self.duct_id not in ducts:
            raise ValueError("integrated network binding references an unknown duct")
        if self.side not in {"left", "right"}:
            raise ValueError("integrated network binding side must be left or right")
        path = ducts[self.duct_id]
        if ((path.role, self.side) not in {("intake", "left"), ("exhaust", "right")}):
            raise ValueError("integrated network volumes may bind only external duct endpoints")
        if path.mesh.areas[0 if self.side == "left" else -1] <= 0.0:
            raise ValueError("integrated network binding requires a positive duct end area")
        expected = ((self.node.id, path.id) if self.side == "left" else
                    (path.id, self.node.id))
        if (self.connection.upstream, self.connection.downstream) != expected:
            raise ValueError("network connection orientation does not match duct endpoint")

    def to_dict(self) -> dict:
        self.node.validate()
        self.connection.validate()
        self.initial_state.validate()
        return {"schema": "INTEGRATED_NETWORK_VOLUME_2T_V1",
                "node": self.node.to_dict(), "connection": self.connection.to_dict(),
                "duct_id": self.duct_id, "side": self.side,
                "initial_state": {"mass_kg": self.initial_state.mass_kg,
                                  "internal_energy_j": self.initial_state.internal_energy_j,
                                  "species_mass_kg": list(self.initial_state.species_mass_kg)}}


class IntegratedEngine2T:
    """One SSPRK2 state for reed/intake-ready, N-transfer, exhaust topology.

    ``geometry(angle_deg)`` must return an :class:`EngineGeometry2T` with exact
    stage volumes and effective areas. CONFIG_V2 supports exactly one intake,
    at least three transfer paths and exactly one exhaust; other role
    cardinalities require a new configuration schema. Boundary conditions are explicit
    existing ``Boundary`` objects. The default atmosphere uses the existing
    P6 composition (fresh air only). Existing prescribed P7 events, when
    configured, contribute species and heat sources to the same cylinder
    stage RHS and are checkpointed with the integrated ledger.
    """
    schema = "MOTORSIM_INTEGRATED_ENGINE_2T_STATE_V7"
    configuration_schema = "MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V2"
    dependency_status = "CONDITIONAL_ON_P4"

    def __init__(self, crankcase_state: tuple, cylinder_state: tuple,
                 ducts: tuple[DuctPath2T, ...], initial_duct_states: dict[str, tuple],
                 geometry: Callable[[float], EngineGeometry2T], *,
                 eos: IdealGas | None = None,
                 species: dict | None = None,
                 atmosphere: tuple = (101325.0, 300.0),
                 atmosphere_species: tuple | None = None,
                 outlet_species: tuple | None = None,
                 inlet_boundary: Boundary | None = None,
                 outlet_boundary: Boundary | None = None,
                 max_cfl: float = 0.4,
                 geometry_identity: dict | None = None,
                 reed_petals: tuple[ReedPetal, ...] = (),
                 port_binding: IntegratedPortBinding2T | None = None,
                 intake_plenum: IntegratedIntakePlenum2T | None = None,
                 network_volumes: tuple[IntegratedNetworkVolume2T, ...] = (),
                 slider_crank: SliderCrankChambers2T | None = None,
                 reference_rpm: float = 1000.0,
                 thermal_system: ThermalSystem | None = None,
                 thermal_locations: dict[str, str] | None = None,
                 thermal_load: float = 0.0,
                 combustion_start_angle_deg: float | None = None):
        initial_crankcase_primitive = tuple(crankcase_state)
        initial_cylinder_primitive = tuple(cylinder_state)
        initial_duct_primitives = deepcopy(initial_duct_states)
        self.eos = eos or IdealGas()
        self.geometry = geometry
        if not isinstance(geometry_identity, dict) or not geometry_identity:
            raise ValueError("stable geometry_identity is required for restart/replay")
        self._source_geometry_identity = deepcopy(geometry_identity)
        try:
            encoded_geometry = json.dumps(geometry_identity, sort_keys=True,
                                          separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("geometry_identity must be finite JSON data") from exc
        self.geometry_sha256 = hashlib.sha256(encoded_geometry.encode("utf-8")).hexdigest()
        if (not isinstance(reed_petals, tuple) or
                any(not isinstance(petal, ReedPetal) for petal in reed_petals)):
            raise ValueError("reed_petals must be a tuple of existing ReedPetal models")
        for petal in reed_petals:
            petal.validate()
        self.reed_petals = reed_petals
        if type(reference_rpm) not in (int, float) or not isfinite(reference_rpm) or reference_rpm <= 0:
            raise ValueError("reference_rpm must be positive and finite")
        self.reference_rpm = float(reference_rpm)
        if type(max_cfl) not in (int, float) or not isfinite(max_cfl) or not 0 < max_cfl <= 1:
            raise ValueError("max_cfl must be finite and in (0, 1]")
        self.max_cfl = float(max_cfl)
        if not callable(geometry):
            raise ValueError("stage geometry callback is required")
        if (not isinstance(ducts, tuple) or len(ducts) < 3 or
                sum(path.role == "intake" for path in ducts) != 1 or
                sum(path.role == "exhaust" for path in ducts) != 1 or
                sum(path.role == "transfer" for path in ducts) < 3):
            raise ValueError(
                "MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V2 supports one intake, "
                "at least three transfer paths and one exhaust")
        for path in ducts:
            path.validate()
        if len({path.id for path in ducts}) != len(ducts):
            raise ValueError("duct ids must be unique")
        self.ducts = ducts
        self.intake = next(path for path in ducts if path.role == "intake")
        self.exhaust = next(path for path in ducts if path.role == "exhaust")
        self.transfers = tuple(path for path in ducts if path.role == "transfer")
        if not isinstance(network_volumes, tuple):
            raise ValueError("network_volumes must be a tuple")
        bindings = list(network_volumes)
        if any(not isinstance(binding, IntegratedNetworkVolume2T)
               for binding in bindings):
            raise ValueError("network_volumes must contain IntegratedNetworkVolume2T bindings")
        if intake_plenum is not None:
            if not isinstance(intake_plenum, IntegratedIntakePlenum2T):
                raise ValueError("intake_plenum must use IntegratedIntakePlenum2T")
            intake_plenum.validate(self.intake)
            bindings.append(IntegratedNetworkVolume2T(
                intake_plenum.node, intake_plenum.connection, self.intake.id,
                "left", intake_plenum.initial_state))
        duct_map = {path.id: path for path in self.ducts}
        for binding in bindings:
            binding.validate(duct_map)
        endpoint_keys = [(binding.duct_id, binding.side) for binding in bindings]
        node_ids = [binding.node.id for binding in bindings]
        connection_ids = [binding.connection.id for binding in bindings]
        if (len(set(endpoint_keys)) != len(endpoint_keys) or
                len(set(node_ids)) != len(node_ids) or
                len(set(connection_ids)) != len(connection_ids)):
            raise ValueError("integrated network node, connection and endpoint ids must be unique")
        self.intake_plenum = intake_plenum
        self.network_volumes = tuple(bindings)
        self.network_volume_by_endpoint = MappingProxyType({
            (binding.duct_id, binding.side): binding for binding in self.network_volumes})
        if port_binding is not None:
            if not isinstance(port_binding, IntegratedPortBinding2T):
                raise ValueError("port_binding must use IntegratedPortBinding2T")
            port_binding.validate(ducts)
        self.port_binding = port_binding
        if slider_crank is not None:
            if not isinstance(slider_crank, SliderCrankChambers2T):
                raise ValueError("slider_crank must use SliderCrankChambers2T")
            slider_crank.validate()
        self.slider_crank = slider_crank
        if set(initial_duct_states) != {path.id for path in ducts}:
            raise ValueError("initial duct states must match topology ids exactly")
        p_atm, t_atm = atmosphere
        if (not all(type(x) in (int, float) and isfinite(x) and x > 0
                    for x in (p_atm, t_atm))):
            raise ValueError("atmosphere pressure and temperature must be positive")
        self.atmosphere_state = self.eos.validate((p_atm / (self.eos.R * t_atm), 0.0,
                                                   p_atm, 1.0))
        self.atmosphere_species = tuple(
            atmospheric_species() if atmosphere_species is None else atmosphere_species)
        validate_species(self.atmosphere_species, 1.0)
        self.outlet_species = tuple(
            atmospheric_species() if outlet_species is None else outlet_species)
        validate_species(self.outlet_species, 1.0)
        self.inlet_boundary = inlet_boundary or Boundary(
            "reservoir", p0=p_atm, T0=t_atm, Y0=1.0)
        self.outlet_boundary = outlet_boundary or Boundary(
            "reservoir", p0=p_atm, T0=t_atm, Y0=1.0)
        self.thermal_system = thermal_system
        self.thermal_load = float(thermal_load)
        if not isfinite(self.thermal_load) or self.thermal_load < 0:
            raise ValueError("thermal load must be finite and nonnegative")
        self.thermal_locations = dict(thermal_locations or {})
        if (combustion_start_angle_deg is not None and
                (type(combustion_start_angle_deg) not in (int, float) or
                 not isfinite(combustion_start_angle_deg) or
                 not 0.0 <= combustion_start_angle_deg < 360.0)):
            raise ValueError("combustion_start_angle_deg must be in [0, 360)")
        self.combustion_start_angle_deg = (
            None if combustion_start_angle_deg is None else
            float(combustion_start_angle_deg))
        self.p7_event: P7BurnEvent | None = None
        self.p7_events: list[dict] = []
        self.p7_heat_added_j = 0.0
        self.p7_source_species_kg = [0.0] * 4
        if self.thermal_system is None:
            if self.thermal_locations:
                raise ValueError("thermal locations require a ThermalSystem")
        else:
            if not isinstance(self.thermal_system, ThermalSystem):
                raise ValueError("thermal_system must be a ThermalSystem")
            self.thermal_system.validate()
            if set(self.thermal_locations) != {surface.id for surface in self.thermal_system.surfaces}:
                raise ValueError("every thermal surface requires one explicit gas location")
            for surface_id, location in self.thermal_locations.items():
                if location in {"cylinder", "crankcase"}:
                    continue
                try:
                    duct_id, cell = location.rsplit(":", 1)
                    path = next(item for item in ducts if item.id == duct_id)
                    cell_index = int(cell)
                except (ValueError, StopIteration, AttributeError) as exc:
                    raise ValueError(
                        f"{surface_id}: duct thermal location must be duct_id:cell_index") from exc
                if cell_index < 0 or cell_index >= len(path.mesh.volumes):
                    raise ValueError(f"{surface_id}: thermal duct cell index is invalid")
        self.angle_deg = 0.0
        self.crank_angle_unwrapped_deg = 0.0
        self.time_s = 0.0
        self.cycle = 0
        self.accepted_steps = 0
        self.rejected_steps = 0
        self.ledger = {"external_mass_kg": 0.0, "external_energy_J": 0.0,
                       "external_species_kg": [0.0] * 4,
                       "fresh_delivered_kg": 0.0,
                       "fresh_short_circuit_kg": 0.0,
                       "fuel_delivered_kg": 0.0,
                       "fuel_short_circuited_kg": 0.0,
                       "heat_to_wall_J": 0.0,
                       "cylinder_work_J": 0.0, "crankcase_work_J": 0.0,
                       "p7_heat_added_J": 0.0,
                       "p7_availability_limited_kg": 0.0,
                       "p7_source_species_kg": [0.0] * 4}
        self.trace = []
        geometry0 = self._geometry(self.angle_deg, self.reference_rpm)
        self.state = {
            "chambers": {
                "crankcase": self._chamber_from_primitive(crankcase_state,
                                                           geometry0.crankcase_volume_m3),
                "cylinder": self._chamber_from_primitive(cylinder_state,
                                                         geometry0.cylinder_volume_m3)},
            "ducts": {}, "network_volumes": {},
            "species": {"chambers": {}, "ducts": {}, "network_volumes": {}},
        }
        for binding in self.network_volumes:
            node = binding.node
            initial = binding.initial_state
            self.state["network_volumes"][node.id] = (
                initial.mass_kg, initial.internal_energy_j, node.volume_m3)
            self.state["species"]["network_volumes"][node.id] = tuple(
                initial.species_mass_kg)
        supplied_species = species or {}
        for name in ("crankcase", "cylinder"):
            mass = self.state["chambers"][name][0]
            values = tuple(supplied_species.get(name, legacy_to_species(mass)))
            self.state["species"]["chambers"][name] = validate_species(values, mass)
        for path in ducts:
            primitive_rows = initial_duct_states[path.id]
            if len(primitive_rows) != len(path.mesh.volumes):
                raise ValueError(f"{path.id}: state/mesh cell count mismatch")
            self.state["ducts"][path.id] = []
            self.state["species"]["ducts"][path.id] = []
            supplied_path = supplied_species.get(path.id)
            if supplied_path is not None and len(supplied_path) != len(primitive_rows):
                raise ValueError(f"{path.id}: species/cell count mismatch")
            for i, primitive in enumerate(primitive_rows):
                rho, velocity, pressure, _ = self.eos.validate(tuple(primitive))
                q = self.eos.conservative((rho, velocity, pressure, 1.0))
                volume = path.mesh.volumes[i]
                self.state["ducts"][path.id].append(q)
                cell_mass = q[0] * volume
                comp = (tuple(supplied_path[i]) if supplied_path is not None else
                        legacy_to_species(cell_mass))
                self.state["species"]["ducts"][path.id].append(
                    validate_species(comp, cell_mass))
        self._validate(self.state)
        self.initial_inventory = self.inventory(self.state)
        self.configuration_identity = self._configuration_identity()
        self._configuration_spec = self._make_configuration_spec(
            initial_crankcase_primitive, initial_cylinder_primitive,
            initial_duct_primitives, atmosphere)
        self._configuration_identity_digest = self._identity_fingerprint()
        self._configuration_guard = self._live_configuration_signature()
        if self.combustion_start_angle_deg == 0.0:
            self.p7_event = capture_event(
                0.0, self.state["species"]["chambers"]["cylinder"])

    def _make_configuration_spec(self, crankcase_primitive, cylinder_primitive,
                                 duct_primitives, atmosphere):
        """Capture a JSON-safe constructor contract for reconstructible geometry.

        V2 intentionally supports only explicit slider-crank volumes and a
        generic port binding. Those two models resolve every geometry field;
        arbitrary callbacks cannot be serialized or represented as reproducible.
        V2 records separate inlet and outlet donor compositions.
        """
        if self.slider_crank is None or self.port_binding is None:
            return None
        return {
            "schema": self.configuration_schema,
            "geometry_contract": "SLIDER_CRANK_AND_GENERIC_PORTS_V1",
            "initial_chambers": {
                "crankcase": list(crankcase_primitive),
                "cylinder": list(cylinder_primitive),
                "species": {name: list(values) for name, values in
                            self.state["species"]["chambers"].items()}},
            "ducts": [{"id": path.id, "role": path.role,
                       "mesh": path.mesh.as_dict()} for path in self.ducts],
            "resolved_topology": {
                "intake": self.intake.id,
                "exhaust": self.exhaust.id,
                "transfers": [path.id for path in self.transfers],
                "network_endpoints": [
                    {"duct_id": duct_id, "side": side,
                     "node_id": binding.node.id,
                     "connection_id": binding.connection.id}
                    for (duct_id, side), binding in sorted(
                        self.network_volume_by_endpoint.items())]},
            "initial_duct_states": {
                path.id: [list(row) for row in duct_primitives[path.id]]
                for path in self.ducts},
            "duct_species": {path.id: [list(row) for row in
                                      self.state["species"]["ducts"][path.id]]
                             for path in self.ducts},
            "eos": {"R": self.eos.R, "gamma": self.eos.gamma},
            "atmosphere": list(atmosphere),
            "atmosphere_species": list(self.atmosphere_species),
            "outlet_species": list(self.outlet_species),
            "boundaries": {"inlet": _jsonify(vars(self.inlet_boundary)),
                           "outlet": _jsonify(vars(self.outlet_boundary))},
            "max_cfl": self.max_cfl,
            "geometry_identity": deepcopy(self._source_geometry_identity),
            "reed_petals": [petal.to_dict() for petal in self.reed_petals],
            "port_binding": self.port_binding.to_dict(),
            "network_volumes": [binding.to_dict()
                                for binding in self.network_volumes],
            "slider_crank": self.slider_crank.to_dict(),
            "reference_rpm": self.reference_rpm,
            "thermal_system": (None if self.thermal_system is None else
                               self.thermal_system.to_dict()),
            "thermal_locations": dict(self.thermal_locations),
            "thermal_load": self.thermal_load,
            "combustion_start_angle_deg": self.combustion_start_angle_deg,
        }

    def configuration_dict(self) -> dict:
        """Return a detached V2 constructor configuration when representable."""
        self._assert_configuration_unchanged(check_identity=True)
        if self._configuration_spec is None:
            raise ValueError(
                "configuration V2 requires explicit slider-crank and generic-port geometry")
        result = deepcopy(self._configuration_spec)
        try:
            json.dumps(result, sort_keys=True, separators=(",", ":"),
                       allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("integrated engine configuration is not finite JSON data") from exc
        return result

    def _live_configuration_signature(self) -> str:
        """Cheaply fingerprint live references/scalars checked before each step."""
        try:
            signature = (
                id(self.eos), self.eos.R, self.eos.gamma,
                tuple((id(path), path.id, path.role, id(path.mesh))
                      for path in self.ducts),
                id(self.intake), id(self.exhaust),
                tuple(id(path) for path in self.transfers),
                tuple(self.atmosphere_state), tuple(self.atmosphere_species),
                tuple(self.outlet_species),
                id(self.inlet_boundary), id(self.outlet_boundary), self.max_cfl,
                self.geometry_sha256, id(self.configuration_identity),
                tuple(id(petal) for petal in self.reed_petals),
                id(self.port_binding),
                None if self.port_binding is None else (
                    id(self.port_binding.port_set), id(self.port_binding.powervalve),
                    tuple(sorted(self.port_binding.path_by_duct.items()))),
                id(self.network_volumes),
                tuple((id(item), id(item.node), id(item.connection),
                       id(item.initial_state), item.duct_id, item.side)
                      for item in self.network_volumes),
                id(self.network_volume_by_endpoint),
                tuple((key, id(item)) for key, item in
                      sorted(self.network_volume_by_endpoint.items())),
                id(self.slider_crank), self.reference_rpm,
                id(self.thermal_system),
                tuple(sorted(self.thermal_locations.items())), self.thermal_load,
                self.combustion_start_angle_deg)
            return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError("live integrated engine configuration is invalid") from exc

    def _identity_fingerprint(self) -> str:
        encoded = json.dumps(self.configuration_identity, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _assert_configuration_unchanged(self, *, check_identity=False) -> None:
        expected = getattr(self, "_configuration_guard", None)
        if expected is not None and self._live_configuration_signature() != expected:
            raise ValueError(
                "integrated engine configuration changed after construction; rebuild the engine")
        if (check_identity and
                self._identity_fingerprint() != self._configuration_identity_digest):
            raise ValueError(
                "integrated engine configuration identity changed after construction")

    def configuration_json(self) -> str:
        """Return canonical compact JSON for the supported constructor contract."""
        return json.dumps(self.configuration_dict(), sort_keys=True,
                          separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_configuration_dict(cls, value: dict) -> "IntegratedEngine2T":
        """Rebuild a supported engine without caller code or geometry callbacks."""
        common_fields = {"schema", "geometry_contract", "initial_chambers", "ducts",
                  "resolved_topology", "initial_duct_states", "duct_species",
                  "eos", "atmosphere",
                  "atmosphere_species", "boundaries", "max_cfl",
                  "geometry_identity", "reed_petals", "port_binding",
                  "network_volumes", "slider_crank", "reference_rpm",
                  "thermal_system", "thermal_locations", "thermal_load",
                  "combustion_start_angle_deg"}
        if not isinstance(value, dict):
            raise ValueError("integrated engine configuration schema is invalid")
        source_schema = value.get("schema")
        legacy_v1 = (source_schema == "MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V1" and
                     set(value) == common_fields)
        current_v2 = (source_schema == cls.configuration_schema and
                      set(value) == common_fields | {"outlet_species"})
        if (not (legacy_v1 or current_v2) or
                value.get("geometry_contract") !=
                "SLIDER_CRANK_AND_GENERIC_PORTS_V1"):
            raise ValueError("integrated engine configuration schema is invalid")
        chambers = value["initial_chambers"]
        if (not isinstance(chambers, dict) or
                set(chambers) != {"crankcase", "cylinder", "species"} or
                not isinstance(chambers["species"], dict) or
                set(chambers["species"]) != {"crankcase", "cylinder"}):
            raise ValueError("integrated engine initial chamber configuration is invalid")
        if (not isinstance(value["ducts"], list) or
                not isinstance(value["initial_duct_states"], dict) or
                not isinstance(value["duct_species"], dict) or
                not isinstance(value["boundaries"], dict) or
                set(value["boundaries"]) != {"inlet", "outlet"}):
            raise ValueError("integrated engine path configuration is invalid")
        from .network_components import NetworkConnection, VolumeGasState, VolumeNode
        from .thermal import ThermalSystem
        from .two_stroke_ports import TwoStrokePortSet

        paths = []
        for row in value["ducts"]:
            if not isinstance(row, dict) or set(row) != {"id", "role", "mesh"}:
                raise ValueError("integrated engine duct configuration is invalid")
            mesh_data = row["mesh"]
            if (not isinstance(mesh_data, dict) or set(mesh_data) !=
                    {"faces", "areas", "volumes", "centers"}):
                raise ValueError("integrated engine mesh configuration is invalid")
            mesh = Mesh(*(tuple(mesh_data[name]) for name in
                          ("faces", "areas", "volumes", "centers")))
            paths.append(DuctPath2T(row["id"], mesh, row["role"]))
        paths = tuple(paths)
        duct_ids = {path.id for path in paths}
        if (set(value["initial_duct_states"]) != duct_ids or
                set(value["duct_species"]) != duct_ids):
            raise ValueError("integrated engine initial duct ids do not match topology")
        binding_data = value["port_binding"]
        if (not isinstance(binding_data, dict) or
                set(binding_data) != {"port_set", "path_by_duct", "powervalve"}):
            raise ValueError("integrated engine port binding configuration is invalid")
        port_set = TwoStrokePortSet.from_dict(binding_data["port_set"])
        valve = (None if binding_data["powervalve"] is None else
                 PowerValve.from_dict(binding_data["powervalve"]))
        binding = IntegratedPortBinding2T(port_set,
                                          binding_data["path_by_duct"], valve)
        slider_data = value["slider_crank"]
        if (not isinstance(slider_data, dict) or
                set(slider_data) != {"schema", "crankcase",
                                     "cylinder_compression_ratio"} or
                slider_data["schema"] != "INTEGRATED_SLIDER_CRANK_CHAMBERS_2T_V1"):
            raise ValueError("integrated engine slider-crank configuration is invalid")
        slider = SliderCrankChambers2T(
            CrankcaseGeometry.from_dict(slider_data["crankcase"]),
            slider_data["cylinder_compression_ratio"])
        network = []
        for row in value["network_volumes"]:
            if (not isinstance(row, dict) or set(row) !=
                    {"schema", "node", "connection", "duct_id", "side",
                     "initial_state"} or
                    row["schema"] != "INTEGRATED_NETWORK_VOLUME_2T_V1"):
                raise ValueError("integrated engine network-volume configuration is invalid")
            initial = row["initial_state"]
            if not isinstance(initial, dict) or set(initial) != {
                    "mass_kg", "internal_energy_j", "species_mass_kg"}:
                raise ValueError("integrated engine network initial state is invalid")
            network.append(IntegratedNetworkVolume2T(
                VolumeNode.from_dict(row["node"]),
                NetworkConnection.from_dict(row["connection"]),
                row["duct_id"], row["side"],
                VolumeGasState(initial["mass_kg"], initial["internal_energy_j"],
                               tuple(initial["species_mass_kg"]))))
        eos_data = value["eos"]
        if not isinstance(eos_data, dict) or set(eos_data) != {"R", "gamma"}:
            raise ValueError("integrated engine EOS configuration is invalid")
        boundary_data = {}
        for name in ("inlet", "outlet"):
            fields_data = value["boundaries"][name]
            if not isinstance(fields_data, dict) or set(fields_data) != {
                    "kind", "state", "p0", "T0", "Y0"}:
                raise ValueError("integrated engine boundary configuration is invalid")
            boundary_data[name] = Boundary(
                fields_data["kind"],
                None if fields_data["state"] is None else
                tuple(fields_data["state"]), fields_data["p0"],
                fields_data["T0"], fields_data["Y0"])
        species = {name: tuple(values) for name, values in
                   chambers["species"].items()}
        species.update({path_id: tuple(tuple(row) for row in rows)
                        for path_id, rows in value["duct_species"].items()})
        thermal = (None if value["thermal_system"] is None else
                   ThermalSystem.from_dict(value["thermal_system"]))

        def resolved_geometry(_angle):
            # Both explicit models replace every returned geometry field.
            return EngineGeometry2T(1.0, 1.0, 0.0, 0.0, 0.0,
                                    tuple(0.0 for _ in
                                          (path for path in paths
                                           if path.role == "transfer")), 0.0)

        engine = cls(
            tuple(chambers["crankcase"]), tuple(chambers["cylinder"]), paths,
            {key: tuple(tuple(row) for row in rows) for key, rows in
             value["initial_duct_states"].items()}, resolved_geometry,
            eos=IdealGas(**eos_data), species=species,
            atmosphere=tuple(value["atmosphere"]),
            atmosphere_species=tuple(value["atmosphere_species"]),
            outlet_species=tuple(value.get("outlet_species",
                                           value["atmosphere_species"])),
            inlet_boundary=boundary_data["inlet"],
            outlet_boundary=boundary_data["outlet"], max_cfl=value["max_cfl"],
            geometry_identity=deepcopy(value["geometry_identity"]),
            reed_petals=tuple(ReedPetal.from_dict(row)
                              for row in value["reed_petals"]),
            port_binding=binding, network_volumes=tuple(network),
            slider_crank=slider, reference_rpm=value["reference_rpm"],
            thermal_system=thermal,
            thermal_locations=deepcopy(value["thermal_locations"]),
            thermal_load=value["thermal_load"],
            combustion_start_angle_deg=value["combustion_start_angle_deg"])
        canonical_input = deepcopy(value)
        canonical_input["schema"] = cls.configuration_schema
        canonical_input["outlet_species"] = list(
            value.get("outlet_species", value["atmosphere_species"]))
        if engine.configuration_dict() != canonical_input:
            raise ValueError("integrated engine resolved topology/configuration mismatch")
        return engine

    def _chamber_from_primitive(self, primitive, volume):
        rho, velocity, pressure, _ = primitive
        if velocity != 0:
            raise ValueError("0D chamber macroscopic velocity must be zero")
        return (rho * volume, pressure * volume / (self.eos.gamma - 1.0), volume)

    def _configuration_identity(self):
        initial_payload = {"state": self.state,
                           "atmosphere": self.atmosphere_state,
                           "atmosphere_species": self.atmosphere_species,
                           "outlet_species": self.outlet_species}
        initial_bytes = json.dumps(initial_payload, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode("utf-8")
        identity = {"ducts": [{"id": path.id, "role": path.role,
                               "mesh": path.mesh.as_dict()} for path in self.ducts],
                    "transfer_ids": [path.id for path in self.transfers],
                    "eos": {"R": self.eos.R, "gamma": self.eos.gamma},
                    "species": list(SPECIES), "state_schema": self.schema,
                    "max_cfl": self.max_cfl, "geometry_sha256": self.geometry_sha256,
                    "reed": [petal.to_dict() for petal in self.reed_petals],
                    "port_binding": (None if self.port_binding is None else
                                     self.port_binding.to_dict()),
                    "network_volumes": [binding.to_dict()
                                        for binding in self.network_volumes],
                    "slider_crank": (None if self.slider_crank is None else
                                     self.slider_crank.to_dict()),
                    "reference_rpm": self.reference_rpm,
                    "initial_state_sha256": hashlib.sha256(initial_bytes).hexdigest(),
                    "boundaries": {"inlet": vars(self.inlet_boundary),
                                   "outlet": vars(self.outlet_boundary)},
                    "thermal": (None if self.thermal_system is None else
                                self.thermal_system.to_dict()),
                    "thermal_locations": self.thermal_locations,
                    "thermal_load": self.thermal_load,
                    "p7": {"schema": "P7_PRESCRIBED_V1",
                           "start_angle_deg": self.combustion_start_angle_deg}}
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                             allow_nan=False)
        normalized = json.loads(encoded)
        normalized["configuration_sha256"] = hashlib.sha256(
            encoded.encode("utf-8")).hexdigest()
        return normalized

    def _geometry(self, angle, rpm=None):
        if self.slider_crank is not None and self.port_binding is not None:
            # These explicit models resolve every field. Do not invoke an
            # otherwise-obsolete caller callback whose behavior is not captured
            # by the reconstructible configuration contract.
            result = EngineGeometry2T(
                1.0, 1.0, 0.0, 0.0, 0.0,
                tuple(0.0 for _ in self.transfers), 0.0)
        else:
            result = self.geometry(float(angle) % 360.0)
            if not isinstance(result, EngineGeometry2T):
                raise ValueError("geometry callback must return EngineGeometry2T")
        if self.slider_crank is not None:
            crankcase_volume, cylinder_volume, crankcase_rate, cylinder_rate = (
                self.slider_crank.resolve(float(angle) % 360.0,
                                          self.reference_rpm if rpm is None else float(rpm)))
            result = EngineGeometry2T(crankcase_volume, cylinder_volume,
                                      crankcase_rate, cylinder_rate,
                                      result.intake_area_m2, result.transfer_areas_m2,
                                      result.exhaust_area_m2)
        if self.port_binding is not None:
            intake, transfers, exhaust = self.port_binding.resolve(
                self.ducts, float(angle) % 360.0,
                self.reference_rpm if rpm is None else float(rpm))
            result = EngineGeometry2T(result.crankcase_volume_m3,
                                      result.cylinder_volume_m3,
                                      result.crankcase_volume_rate_m3_s,
                                      result.cylinder_volume_rate_m3_s,
                                      intake, transfers, exhaust)
        result.validate(tuple(path.id for path in self.transfers) if hasattr(self, "transfers")
                        else tuple(path.id for path in self.ducts if path.role == "transfer"))
        return result

    def _chamber_state(self, chamber, species):
        mass, energy, volume = chamber
        if mass <= 0 or energy <= 0 or volume <= 0:
            raise ValueError("inadmissible 0D chamber state")
        pressure = (self.eos.gamma - 1.0) * energy / volume
        fresh_fraction = fsum(self._fractions(species, mass)[:2])
        return ChamberState(mass, energy, mass * fresh_fraction, volume)

    def _primitive(self, q):
        return self.eos.primitive((q[0], q[1], q[2], q[0]))

    @staticmethod
    def _fractions(species, mass):
        values = validate_species(species, mass)
        total = fsum(values)
        if total == 0.0:
            return (0.0, 0.0, 0.0, 0.0)
        # Species masses remain untouched. Normalizing by their validated sum
        # keeps EOS composition in [0, 1] when gas/species totals differ only
        # by accepted floating-point roundoff.
        return tuple(value / total for value in values)

    def _face_species_flux(self, mass_flux, left_species, left_mass,
                           right_species, right_mass):
        donor_left = self._fractions(left_species, left_mass)
        donor_right = self._fractions(right_species, right_mass)
        return donor_species(mass_flux, donor_left, donor_right)

    def _limit_p7_stage_source(self, state, assembled, dt_s):
        """Bound the prescribed P7 sink by reactant mass in this SSPRK stage.

        This is an availability limiter for the new integrated coupling only;
        it does not alter the historical P7 source law. Any limited mass is
        explicit in the accepted-stage trace and global ledger.
        """
        requested = tuple(assembled["p7_species_rate"])
        scale = 1.0
        if any(requested[index] < 0.0 for index in (0, 1)):
            species = state["species"]["chambers"]["cylinder"]
            full_rhs = assembled["species"]["chambers"]["cylinder"]
            for index in (0, 1):
                if requested[index] >= 0.0:
                    continue
                non_p7_rate = full_rhs[index] - requested[index]
                available_without_p7 = species[index] + dt_s * non_p7_rate
                allowed = max(0.0, available_without_p7) / (-dt_s * requested[index])
                scale = min(scale, max(0.0, min(1.0, allowed)))
        applied = tuple(value * scale for value in requested)
        # A sink is negative.  The unapplied portion is the requested sink
        # magnitude minus the accepted sink magnitude: -requested + applied.
        # Subtracting ``applied`` here double-counted every unscaled sink.
        limited = max(0.0, -requested[0] + applied[0]) + max(
            0.0, -requested[1] + applied[1])
        heat_limited = 0.0
        if scale < 1.0:
            rhs_species = assembled["species"]["chambers"]["cylinder"]
            assembled["species"]["chambers"]["cylinder"] = tuple(
                rhs_species[index] + applied[index] - requested[index]
                for index in range(4))
            requested_heat = assembled["p7_heat_rate"]
            applied_heat = requested_heat * scale
            assembled["q"]["chambers"]["cylinder"][1] += (
                applied_heat - requested_heat)
            assembled["p7_species_rate"] = applied
            assembled["p7_heat_rate"] = applied_heat
            heat_limited = requested_heat - applied_heat
        limitation = {"scale": scale, "limited_reactant_rate_kg_s": limited,
                      "limited_heat_rate_W": heat_limited}
        assembled["p7_limiter"] = limitation
        return limitation

    def _external_face(self, state, path, side, boundary):
        cells = state["ducts"][path.id]
        species = state["species"]["ducts"][path.id]
        index = 0 if side == "left" else -1
        primitive = self._primitive(cells[index])
        normal = -1 if side == "left" else 1
        flux, speeds, _ = boundary.flux(primitive, normal, self.eos)
        area = path.mesh.areas[0 if side == "left" else -1]
        face = tuple(area * value for value in flux[:3])
        if side == "left":
            left_comp = self.atmosphere_species
            left_mass = 1.0
            right_comp = species[index]
            right_mass = cells[index][0] * path.mesh.volumes[index]
        else:
            left_comp = species[index]
            left_mass = cells[index][0] * path.mesh.volumes[index]
            right_comp = self.outlet_species
            right_mass = 1.0
        species_flux = self._face_species_flux(face[0], left_comp, left_mass,
                                               right_comp, right_mass)
        return face, species_flux, max(abs(speeds[0]), abs(speeds[-1]))

    def _network_face(self, state, path, side, primitive, cell_species, cell_mass):
        binding = self.network_volume_by_endpoint.get((path.id, side))
        if binding is None:
            return None
        node = binding.node
        volume_state = VolumeGasState(
            *state["network_volumes"][node.id][:2],
            tuple(state["species"]["network_volumes"][node.id]))
        face_index = 0 if side == "left" else -1
        exchange_area = min(binding.connection.area_m2, path.mesh.areas[face_index])
        exchange = resolve_volume_duct_interface(
            volume_state, node.volume_m3, primitive,
            self._fractions(cell_species, cell_mass), exchange_area,
            -1 if side == "left" else 1, eos=self.eos)
        # Convert the node-oriented exchange once into geometric +x face order.
        sign = -1.0 if side == "left" else 1.0
        face = (sign * exchange.mass_into_volume_kg_s,
                sign * exchange.axial_impulse_into_volume_n,
                sign * exchange.energy_into_volume_w)
        species = tuple(sign * value for value in
                        exchange.species_into_volume_kg_s)
        speed = max(abs(exchange.wave_speeds[0]), abs(exchange.wave_speeds[-1]))
        return binding, exchange, face, species, speed

    def _assemble(self, state, angle, rpm, p7_event=_USE_ACTIVE_P7_EVENT):
        """Build every RHS from one immutable stage state."""
        g = self._geometry(angle, rpm)
        chambers = state["chambers"]
        species_chambers = state["species"]["chambers"]
        cc = self._chamber_state(chambers["crankcase"], species_chambers["crankcase"])
        cy = self._chamber_state(chambers["cylinder"], species_chambers["cylinder"])
        rhs_q = {"chambers": {"crankcase": [0.0, 0.0, 0.0],
                               "cylinder": [0.0, 0.0, 0.0]},
                 "ducts": {}, "network_volumes": {}}
        chamber_outflow = {"crankcase": 0.0, "cylinder": 0.0}
        rhs_s = {"chambers": {"crankcase": [0.0] * 4,
                               "cylinder": [0.0] * 4},
                 "ducts": {}, "network_volumes": {}}
        network_outflow = {}
        network_exchanges = {}
        faces_trace = {}
        external = {"mass": 0.0, "energy": 0.0, "species": [0.0] * 4}
        fresh_air_intake_delivered_rate = 0.0
        fresh_delivered_rate = 0.0
        fresh_short_circuit_rate = 0.0
        fuel_delivered_rate = 0.0
        fuel_short_circuited_rate = 0.0
        thermal_rates = {}
        work = {"crankcase": -((self.eos.gamma - 1) * cc.internal_energy / cc.volume) *
                g.crankcase_volume_rate_m3_s,
                "cylinder": -((self.eos.gamma - 1) * cy.internal_energy / cy.volume) *
                g.cylinder_volume_rate_m3_s}
        for path in self.ducts:
            qs = state["ducts"][path.id]
            ss = state["species"]["ducts"][path.id]
            primitives = [self._primitive(q) for q in qs]
            if path.role == "intake":
                network = self._network_face(
                    state, path, "left", primitives[0], ss[0],
                    qs[0][0] * path.mesh.volumes[0])
                if network is None:
                    external_l, species_l, speed_l = self._external_face(
                        state, path, "left", self.inlet_boundary)
                else:
                    binding, exchange, external_l, species_l, speed_l = network
                    node_id = binding.node.id
                    rhs_q["network_volumes"][node_id] = [
                        exchange.mass_into_volume_kg_s,
                        exchange.energy_into_volume_w]
                    rhs_s["network_volumes"][node_id] = list(
                        exchange.species_into_volume_kg_s)
                    network_outflow[node_id] = max(
                        0.0, -exchange.mass_into_volume_kg_s)
                    network_exchanges[node_id] = {
                        "connection_id": binding.connection.id,
                        "mass_into_volume_kg_s": exchange.mass_into_volume_kg_s,
                        "energy_into_volume_w": exchange.energy_into_volume_w,
                        "species_into_volume_kg_s": exchange.species_into_volume_kg_s,
                        "axial_impulse_into_volume_n": exchange.axial_impulse_into_volume_n,
                        "wave_speeds": exchange.wave_speeds,
                        "fallback_reason": exchange.fallback_reason}
                intake_reed_area = g.intake_area_m2
                if self.reed_petals:
                    intake_reed_area = min(
                        intake_reed_area,
                        static_area(self.reed_petals,
                                    primitives[-1][2] -
                                    cc.thermodynamics(self.eos)[1]))
                intake_area = min(intake_reed_area, path.mesh.areas[-1])
                right_exchange = interface_flux(cc, primitives[-1], intake_area, 1,
                                                eos=self.eos) if intake_area else None
                right_face = _port_face_flux(
                    right_exchange, primitives[-1], path.mesh.areas[-1], intake_area)
                speed_r = (max(abs(primitives[-1][1] - self.eos.sound_speed(primitives[-1])),
                               abs(primitives[-1][1] + self.eos.sound_speed(primitives[-1])))
                           if right_exchange is None else
                           max(abs(right_exchange.wave_speeds[0]),
                               abs(right_exchange.wave_speeds[-1])))
                right_species = ((0.0,) * 4 if right_exchange is None else
                    self._face_species_flux(right_face[0], ss[-1], qs[-1][0]*path.mesh.volumes[-1],
                                            species_chambers["crankcase"], chambers["crankcase"][0]))
                # A left face points in +x; it is an external inflow when positive.
                if network is None:
                    external["mass"] += external_l[0]
                    external["energy"] += external_l[2]
                    for j, value in enumerate(species_l): external["species"][j] += value
                fresh_air_intake_delivered_rate += max(0.0, species_l[0])
                fuel_delivered_rate += max(0.0, species_l[1])
                if right_exchange is not None:
                    chamber_outflow["crankcase"] += max(0.0, -right_exchange.outward[0])
                    rhs_q["chambers"]["crankcase"][0] += right_exchange.outward[0]
                    rhs_q["chambers"]["crankcase"][1] += right_exchange.outward[2]
                    for j, value in enumerate(right_species): rhs_s["chambers"]["crankcase"][j] += value
                left_face, left_species = external_l, species_l
                right_face_species = right_species
                faces_trace[path.id] = {"left": external_l, "right": right_face,
                                        "left_species": species_l,
                                        "right_species": right_species,
                                        "left_speed": speed_l, "right_speed": speed_r}
                faces_trace[path.id]["effective_reed_area_m2"] = intake_area
            elif path.role == "transfer":
                index = next(i for i, item in enumerate(self.transfers) if item.id == path.id)
                port_area = g.transfer_areas_m2[index]
                left_area = min(port_area, path.mesh.areas[0])
                right_area = min(port_area, path.mesh.areas[-1])
                left_exchange = interface_flux(cc, primitives[0], left_area, -1,
                                               eos=self.eos) if left_area else None
                right_exchange = interface_flux(cy, primitives[-1], right_area, 1,
                                                eos=self.eos) if right_area else None
                left_face = _port_face_flux(
                    left_exchange, primitives[0], path.mesh.areas[0], left_area)
                right_face = _port_face_flux(
                    right_exchange, primitives[-1], path.mesh.areas[-1], right_area)
                speed_l = (max(abs(primitives[0][1] - self.eos.sound_speed(primitives[0])),
                               abs(primitives[0][1] + self.eos.sound_speed(primitives[0])))
                           if left_exchange is None else
                           max(abs(left_exchange.wave_speeds[0]), abs(left_exchange.wave_speeds[-1])))
                speed_r = (max(abs(primitives[-1][1] - self.eos.sound_speed(primitives[-1])),
                               abs(primitives[-1][1] + self.eos.sound_speed(primitives[-1])))
                           if right_exchange is None else
                           max(abs(right_exchange.wave_speeds[0]), abs(right_exchange.wave_speeds[-1])))
                left_species = ((0.0,) * 4 if left_exchange is None else
                    self._face_species_flux(left_face[0], species_chambers["crankcase"],
                                            chambers["crankcase"][0], ss[0],
                                            qs[0][0]*path.mesh.volumes[0]))
                right_species = ((0.0,) * 4 if right_exchange is None else
                    self._face_species_flux(right_face[0], ss[-1], qs[-1][0]*path.mesh.volumes[-1],
                                            species_chambers["cylinder"], chambers["cylinder"][0]))
                if right_exchange is not None:
                    fresh_delivered_rate += max(0.0, right_species[0] + right_species[1])
                for endpoint, exchange, sflux in (("crankcase", left_exchange,
                                                    tuple(-value for value in left_species)),
                                                   ("cylinder", right_exchange, right_species)):
                    if exchange is None: continue
                    chamber_outflow[endpoint] += max(0.0, -exchange.outward[0])
                    rhs_q["chambers"][endpoint][0] += exchange.outward[0]
                    rhs_q["chambers"][endpoint][1] += exchange.outward[2]
                    for j, value in enumerate(sflux): rhs_s["chambers"][endpoint][j] += value
                right_face_species = right_species
                faces_trace[path.id] = {"left": left_face, "right": right_face,
                                        "left_species": left_species,
                                        "right_species": right_species,
                                        "left_speed": speed_l, "right_speed": speed_r}
            else:
                exhaust_area = min(g.exhaust_area_m2, path.mesh.areas[0])
                left_exchange = interface_flux(cy, primitives[0], exhaust_area, -1,
                                               eos=self.eos) if exhaust_area else None
                network = self._network_face(
                    state, path, "right", primitives[-1], ss[-1],
                    qs[-1][0] * path.mesh.volumes[-1])
                if network is None:
                    external_r, species_r, speed_r = self._external_face(
                        state, path, "right", self.outlet_boundary)
                else:
                    binding, exchange, external_r, species_r, speed_r = network
                    node_id = binding.node.id
                    rhs_q["network_volumes"][node_id] = [
                        exchange.mass_into_volume_kg_s,
                        exchange.energy_into_volume_w]
                    rhs_s["network_volumes"][node_id] = list(
                        exchange.species_into_volume_kg_s)
                    network_outflow[node_id] = max(
                        0.0, -exchange.mass_into_volume_kg_s)
                    network_exchanges[node_id] = {
                        "connection_id": binding.connection.id,
                        "mass_into_volume_kg_s": exchange.mass_into_volume_kg_s,
                        "energy_into_volume_w": exchange.energy_into_volume_w,
                        "species_into_volume_kg_s": exchange.species_into_volume_kg_s,
                        "axial_impulse_into_volume_n": exchange.axial_impulse_into_volume_n,
                        "wave_speeds": exchange.wave_speeds,
                        "fallback_reason": exchange.fallback_reason}
                left_face = _port_face_flux(
                    left_exchange, primitives[0], path.mesh.areas[0], exhaust_area)
                speed_l = (max(abs(primitives[0][1] - self.eos.sound_speed(primitives[0])),
                               abs(primitives[0][1] + self.eos.sound_speed(primitives[0])))
                           if left_exchange is None else
                           max(abs(left_exchange.wave_speeds[0]), abs(left_exchange.wave_speeds[-1])))
                left_species = ((0.0,) * 4 if left_exchange is None else
                    self._face_species_flux(left_face[0], species_chambers["cylinder"],
                                            chambers["cylinder"][0], ss[0],
                                            qs[0][0]*path.mesh.volumes[0]))
                if left_exchange is not None:
                    fresh_short_circuit_rate += _gross_fresh_short_circuit_rate(
                        g.exhaust_area_m2, g.transfer_areas_m2, left_species)
                    if (g.exhaust_area_m2 > 0.0 and
                            any(area > 0.0 for area in g.transfer_areas_m2)):
                        fuel_short_circuited_rate += max(0.0, left_species[1])
                if left_exchange is not None:
                    chamber_outflow["cylinder"] += max(0.0, -left_exchange.outward[0])
                    rhs_q["chambers"]["cylinder"][0] += left_exchange.outward[0]
                    rhs_q["chambers"]["cylinder"][1] += left_exchange.outward[2]
                    for j, value in enumerate(left_species): rhs_s["chambers"]["cylinder"][j] -= value
                if network is None:
                    external["mass"] -= external_r[0]
                    external["energy"] -= external_r[2]
                    for j, value in enumerate(species_r): external["species"][j] -= value
                right_face, right_face_species = external_r, species_r
                faces_trace[path.id] = {"left": left_face, "right": external_r,
                                        "left_species": left_species,
                                        "right_species": species_r,
                                        "left_speed": speed_l, "right_speed": speed_r}
            faces = [left_face]
            species_faces = [left_species]
            face_speeds = [speed_l]
            for i, (a, b) in enumerate(zip(primitives, primitives[1:])):
                flux, waves, _ = hllc_flux(a, b, self.eos)
                area = path.mesh.areas[i + 1]
                gas_face = tuple(area * value for value in flux[:3])
                mflux = gas_face[0]
                # Keep states in geometric left/right order.  The shared donor
                # selector inside _face_species_flux chooses right for reverse
                # flow; preselecting here would reverse that decision twice.
                left_mass = qs[i][0] * path.mesh.volumes[i]
                right_mass = qs[i + 1][0] * path.mesh.volumes[i + 1]
                sf = self._face_species_flux(mflux, ss[i], left_mass,
                                             ss[i + 1], right_mass)
                faces.append(gas_face); species_faces.append(sf)
                face_speeds.append(max(abs(waves[0]), abs(waves[-1])))
            faces.append(right_face); species_faces.append(right_face_species)
            face_speeds.append(speed_r)
            dq, ds = [], []
            for i, (q, comp) in enumerate(zip(qs, ss)):
                vol = path.mesh.volumes[i]
                rhs = [-(faces[i+1][k]-faces[i][k])/vol for k in range(3)]
                # Existing quasi-1D solver's geometric pressure source.
                rhs[1] += primitives[i][2] * (
                    path.mesh.areas[i+1] - path.mesh.areas[i]) / vol
                dq.append(tuple(rhs))
                ds.append(tuple(-(species_faces[i+1][j]-species_faces[i][j]) for j in range(4)))
            rhs_q["ducts"][path.id] = dq
            rhs_s["ducts"][path.id] = ds
            faces_trace[path.id]["all_faces"] = faces
            faces_trace[path.id]["all_species_faces"] = species_faces
            faces_trace[path.id]["face_speeds"] = face_speeds
        for name in ("crankcase", "cylinder"):
            rhs_q["chambers"][name][1] += work[name]
        p7_species_rate = (0.0, 0.0, 0.0, 0.0)
        p7_heat_rate = 0.0
        stage_p7_event = (self.p7_event if p7_event is _USE_ACTIVE_P7_EVENT else
                          p7_event)
        if stage_p7_event is not None:
            p7_source = stage_p7_event.source(float(angle), float(rpm) * 6.0)
            p7_species_rate = tuple(p7_source[:4])
            p7_heat_rate = p7_source[4]
            for index, rate in enumerate(p7_species_rate):
                rhs_s["chambers"]["cylinder"][index] += rate
            rhs_q["chambers"]["cylinder"][1] += p7_heat_rate
        if self.thermal_system is not None:
            for surface in self.thermal_system.surfaces:
                location = self.thermal_locations[surface.id]
                if location in ("crankcase", "cylinder"):
                    mass, energy, volume = chambers[location]
                    gas_temperature = energy / (mass * self.eos.cv)
                    heat = self.thermal_system.heat_rate_w(
                        surface.id, gas_temperature, rpm, self.thermal_load)
                    rhs_q["chambers"][location][1] -= heat
                else:
                    duct_id, cell_text = location.rsplit(":", 1)
                    cell_index = int(cell_text)
                    path = next(item for item in self.ducts if item.id == duct_id)
                    q = state["ducts"][duct_id][cell_index]
                    primitive = self._primitive(q)
                    gas_temperature = primitive[2] / (primitive[0] * self.eos.R)
                    heat = self.thermal_system.heat_rate_w(
                        surface.id, gas_temperature, rpm, self.thermal_load)
                    rhs_q["ducts"][duct_id][cell_index] = list(
                        rhs_q["ducts"][duct_id][cell_index])
                    rhs_q["ducts"][duct_id][cell_index][2] -= heat / path.mesh.volumes[cell_index]
                    rhs_q["ducts"][duct_id][cell_index] = tuple(
                        rhs_q["ducts"][duct_id][cell_index])
                thermal_rates[surface.id] = heat
        return {"q": rhs_q, "species": rhs_s, "geometry": g,
                "chamber_outflow_kg_s": chamber_outflow,
                "network_outflow_kg_s": network_outflow,
                "network_exchanges": network_exchanges,
                "external": external, "work_rates": work,
                "fresh_air_intake_delivered_rate": fresh_air_intake_delivered_rate,
                "fresh_delivered_rate": fresh_delivered_rate,
                "fresh_short_circuit_rate": fresh_short_circuit_rate,
                "fuel_delivered_rate": fuel_delivered_rate,
                "fuel_short_circuited_rate": fuel_short_circuited_rate,
                "p7_species_rate": p7_species_rate,
                "p7_heat_rate": p7_heat_rate,
                "thermal_rates": thermal_rates,
                "faces": faces_trace}

    def _cfl(self, state, assembled, dt_s):
        values = []
        for path in self.ducts:
            face_speeds = assembled["faces"][path.id]["face_speeds"]
            for i, (q, width) in enumerate(zip(state["ducts"][path.id], path.mesh.widths)):
                rho, velocity, pressure, _ = self._primitive(q)
                sound = self.eos.sound_speed((rho, velocity, pressure, 1.0))
                signal = abs(velocity) + sound
                first = width / signal
                denominator = (path.mesh.areas[i] * face_speeds[i] +
                               path.mesh.areas[i+1] * face_speeds[i+1])
                second = (2.0 * path.mesh.volumes[i] / denominator
                          if denominator > 0 else float("inf"))
                values.append(float(dt_s) / min(first, second))
        # A connected 0D chamber has no mesh width. Bound gross outward flux
        # (not net flux, which could hide simultaneous inflow/outflow) so a
        # small chamber cannot be emptied in one SSPRK stage.
        for name in ("crankcase", "cylinder"):
            mass = state["chambers"][name][0]
            outflow_rate = assembled["chamber_outflow_kg_s"][name]
            values.append(float(dt_s) * outflow_rate / mass)
        for node_id, outflow_rate in assembled["network_outflow_kg_s"].items():
            mass = state["network_volumes"][node_id][0]
            values.append(float(dt_s) * outflow_rate / mass)
        maximum = max(values, default=0.0)
        if maximum > self.max_cfl:
            self.rejected_steps += 1
            raise ValueError(f"CFL limit exceeded: {maximum:.9g} > {self.max_cfl:.9g}")
        return maximum

    def _validate(self, state):
        for name, chamber in state["chambers"].items():
            mass, energy, volume = chamber
            comp = validate_species(state["species"]["chambers"][name], mass)
            if min(mass, energy, volume) <= 0:
                raise ValueError(f"{name} state is inadmissible")
            pressure = (self.eos.gamma - 1.0) * energy / volume
            fractions = self._fractions(comp, mass)
            self.eos.validate((mass/volume, 0.0, pressure,
                               fsum(fractions[:2])))
        for path in self.ducts:
            for i, q in enumerate(state["ducts"][path.id]):
                volume = path.mesh.volumes[i]
                self.eos.primitive((q[0], q[1], q[2], q[0]))
                validate_species(state["species"]["ducts"][path.id][i], q[0]*volume)
        expected_node_ids = {binding.node.id for binding in self.network_volumes}
        if (set(state.get("network_volumes", {})) != expected_node_ids or
                set(state["species"].get("network_volumes", {})) != expected_node_ids):
            raise ValueError("integrated network volume state identity mismatch")
        for binding in self.network_volumes:
            node_id = binding.node.id
            chamber = state["network_volumes"].get(node_id)
            species = state["species"].get("network_volumes", {}).get(node_id)
            if (not isinstance(chamber, (tuple, list)) or len(chamber) != 3 or
                    chamber[2] != binding.node.volume_m3):
                raise ValueError("integrated network volume geometry mismatch")
            if (any(type(value) not in (int, float) or not isfinite(value)
                    for value in chamber) or
                    not isinstance(species, (tuple, list)) or len(species) != 4 or
                    any(type(value) not in (int, float) or not isfinite(value)
                        for value in species)):
                raise ValueError("integrated network volume state contains invalid values")
            mass, energy, volume = chamber
            comp = validate_species(species, mass)
            if min(mass, energy, volume) <= 0:
                raise ValueError("integrated network volume state is inadmissible")
            pressure = (self.eos.gamma - 1.0) * energy / volume
            fractions = self._fractions(comp, mass)
            self.eos.validate((mass/volume, 0.0, pressure,
                               fsum(fractions[:2])))

    def _combine(self, base, rhs0, rhs1, dt, angle):
        result = deepcopy(base)
        g = self._geometry(angle)
        for name, volume in (("crankcase", g.crankcase_volume_m3),
                             ("cylinder", g.cylinder_volume_m3)):
            q0 = base["chambers"][name]
            a, b = rhs0["q"]["chambers"][name], rhs1["q"]["chambers"][name]
            result["chambers"][name] = tuple(q0[i] + .5*dt*(a[i]+b[i])
                                               for i in range(2)) + (volume,)
            s0 = base["species"]["chambers"][name]
            sa, sb = rhs0["species"]["chambers"][name], rhs1["species"]["chambers"][name]
            result["species"]["chambers"][name] = tuple(s0[i]+.5*dt*(sa[i]+sb[i])
                                                          for i in range(4))
        for path in self.ducts:
            q0 = base["ducts"][path.id]
            qa, qb = rhs0["q"]["ducts"][path.id], rhs1["q"]["ducts"][path.id]
            result["ducts"][path.id] = [tuple(q0[i][k]+.5*dt*(qa[i][k]+qb[i][k])
                                                for k in range(3)) + (0.0,)
                                        for i in range(len(q0))]
            s0 = base["species"]["ducts"][path.id]
            sa, sb = rhs0["species"]["ducts"][path.id], rhs1["species"]["ducts"][path.id]
            result["species"]["ducts"][path.id] = [tuple(s0[i][j]+.5*dt*(sa[i][j]+sb[i][j])
                                                            for j in range(4))
                                                    for i in range(len(s0))]
            for i, q in enumerate(result["ducts"][path.id]):
                mass_density = fsum(result["species"]["ducts"][path.id][i]) / path.mesh.volumes[i]
                result["ducts"][path.id][i] = (q[0], q[1], q[2], mass_density)
        for node_id, q0 in base["network_volumes"].items():
            a, b = rhs0["q"]["network_volumes"][node_id], rhs1["q"]["network_volumes"][node_id]
            result["network_volumes"][node_id] = (
                q0[0] + .5*dt*(a[0]+b[0]),
                q0[1] + .5*dt*(a[1]+b[1]), q0[2])
            s0 = base["species"]["network_volumes"][node_id]
            sa = rhs0["species"]["network_volumes"][node_id]
            sb = rhs1["species"]["network_volumes"][node_id]
            result["species"]["network_volumes"][node_id] = tuple(
                s0[j] + .5*dt*(sa[j]+sb[j]) for j in range(4))
        return result

    def inventory(self, state=None):
        state = self.state if state is None else state
        mass = energy = 0.0
        species = [0.0] * 4
        for name, q in state["chambers"].items():
            mass += q[0]; energy += q[1]
            for j, value in enumerate(state["species"]["chambers"][name]): species[j] += value
        for path in self.ducts:
            for q, comp, volume in zip(state["ducts"][path.id],
                                       state["species"]["ducts"][path.id],
                                       path.mesh.volumes):
                mass += q[0] * volume; energy += q[2] * volume
                for j, value in enumerate(comp): species[j] += value
        for node_id, q in state["network_volumes"].items():
            mass += q[0]; energy += q[1]
            for j, value in enumerate(state["species"]["network_volumes"][node_id]):
                species[j] += value
        return {"mass_kg": mass, "energy_J": energy, "species_kg": tuple(species)}

    def step(self, dt_s: float, delta_angle_deg: float):
        self._assert_configuration_unchanged()
        if (type(dt_s) not in (int, float) or not isfinite(dt_s) or dt_s <= 0 or
                type(delta_angle_deg) not in (int, float) or not isfinite(delta_angle_deg)
                or delta_angle_deg <= 0):
            raise ValueError("time and crank-angle increments must be positive finite values")
        start_angle = self.crank_angle_unwrapped_deg
        end_angle = start_angle + float(delta_angle_deg)
        step_p7_event = self.p7_event
        archived_p7_event = None
        if self.combustion_start_angle_deg is not None:
            cycle_ignition = (int(start_angle // 360.0) * 360.0 +
                              self.combustion_start_angle_deg)
            if cycle_ignition > start_angle + 1e-10:
                ignition = cycle_ignition
            else:
                ignition = cycle_ignition + 360.0
            boundaries = [ignition, ignition + 40.0]
            if (self.p7_event is not None and
                    self.p7_event.start + 40.0 > start_angle + 1e-10):
                boundaries.append(self.p7_event.start + 40.0)
            if any(start_angle + 1e-10 < boundary < end_angle - 1e-10
                   for boundary in boundaries):
                raise ValueError(
                    "P7 integrated steps must end exactly at ignition and the fixed 40-degree event boundary")
            if (self.p7_event is None and
                    start_angle > cycle_ignition + 1e-10):
                raise ValueError("P7 event start was skipped; align steps to its ignition angle")
            if abs(start_angle - cycle_ignition) <= 1e-10:
                if (step_p7_event is None or
                        abs(step_p7_event.start - cycle_ignition) > 1e-10):
                    if step_p7_event is not None:
                        archived_p7_event = snapshot_event(step_p7_event)
                    step_p7_event = capture_event(
                        cycle_ignition,
                        self.state["species"]["chambers"]["cylinder"])
        q0 = deepcopy(self.state)
        self._validate(q0)
        rpm = float(delta_angle_deg) / (6.0 * float(dt_s))
        r0 = self._assemble(q0, start_angle, rpm, step_p7_event)
        limiter0 = self._limit_p7_stage_source(q0, r0, float(dt_s))
        cfl0 = self._cfl(q0, r0, float(dt_s))
        q1 = deepcopy(q0)
        for name in ("crankcase", "cylinder"):
            q = q0["chambers"][name]
            rhs = r0["q"]["chambers"][name]
            geom_volume = (r0["geometry"].crankcase_volume_m3 if name == "crankcase" else
                           r0["geometry"].cylinder_volume_m3)
            q1["chambers"][name] = (q[0]+dt_s*rhs[0], q[1]+dt_s*rhs[1], geom_volume)
            q1["species"]["chambers"][name] = tuple(
                q0["species"]["chambers"][name][j] + dt_s*r0["species"]["chambers"][name][j]
                for j in range(4))
        for path in self.ducts:
            q1["ducts"][path.id] = []
            q1["species"]["ducts"][path.id] = []
            for i, (q, rhs) in enumerate(zip(q0["ducts"][path.id], r0["q"]["ducts"][path.id])):
                q1["ducts"][path.id].append(tuple(q[k]+dt_s*rhs[k] for k in range(3)) + (0.0,))
                q1["species"]["ducts"][path.id].append(tuple(
                    q0["species"]["ducts"][path.id][i][j] +
                    dt_s*r0["species"]["ducts"][path.id][i][j] for j in range(4)))
        for node_id, q in q0["network_volumes"].items():
            rhs_q = r0["q"]["network_volumes"][node_id]
            rhs_species = r0["species"]["network_volumes"][node_id]
            q1["network_volumes"][node_id] = (
                q[0] + dt_s*rhs_q[0], q[1] + dt_s*rhs_q[1], q[2])
            q1["species"]["network_volumes"][node_id] = tuple(
                q0["species"]["network_volumes"][node_id][j] +
                dt_s*rhs_species[j] for j in range(4))
        g1 = self._geometry(end_angle)
        q1["chambers"]["crankcase"] = (*q1["chambers"]["crankcase"][:2], g1.crankcase_volume_m3)
        q1["chambers"]["cylinder"] = (*q1["chambers"]["cylinder"][:2], g1.cylinder_volume_m3)
        for path in self.ducts:
            for i, q in enumerate(q1["ducts"][path.id]):
                rho = fsum(q1["species"]["ducts"][path.id][i])/path.mesh.volumes[i]
                q1["ducts"][path.id][i] = (q[0], q[1], q[2], rho)
        self._validate(q1)
        r1 = self._assemble(q1, end_angle, rpm, step_p7_event)
        limiter1 = self._limit_p7_stage_source(q1, r1, float(dt_s))
        cfl1 = self._cfl(q1, r1, float(dt_s))
        qn = self._combine(q0, r0, r1, float(dt_s), end_angle)
        self._validate(qn)
        for key in ("mass", "energy"):
            increment = .5*dt_s*(r0["external"][key]+r1["external"][key])
            self.ledger["external_mass_kg" if key == "mass" else "external_energy_J"] += increment
        for j in range(4):
            self.ledger["external_species_kg"][j] += .5*dt_s*(
                r0["external"]["species"][j]+r1["external"]["species"][j])
        self.ledger["fresh_delivered_kg"] += .5*dt_s*(
            r0["fresh_delivered_rate"]+r1["fresh_delivered_rate"])
        self.ledger["fresh_short_circuit_kg"] += .5*dt_s*(
            r0["fresh_short_circuit_rate"]+r1["fresh_short_circuit_rate"])
        self.ledger["fuel_delivered_kg"] += .5*dt_s*(
            r0["fuel_delivered_rate"]+r1["fuel_delivered_rate"])
        self.ledger["fuel_short_circuited_kg"] += .5*dt_s*(
            r0["fuel_short_circuited_rate"]+r1["fuel_short_circuited_rate"])
        wall_rates_0, wall_rates_1 = r0["thermal_rates"], r1["thermal_rates"]
        if set(wall_rates_0) != set(wall_rates_1):
            raise ValueError("thermal surface set changed between SSPRK2 stages")
        heat_to_wall = .5*dt_s*fsum(wall_rates_0.values()) + .5*dt_s*fsum(wall_rates_1.values())
        self.ledger["heat_to_wall_J"] += heat_to_wall
        self.ledger["crankcase_work_J"] += .5*dt_s*(r0["work_rates"]["crankcase"]+
                                                     r1["work_rates"]["crankcase"])
        self.ledger["cylinder_work_J"] += .5*dt_s*(r0["work_rates"]["cylinder"]+
                                                   r1["work_rates"]["cylinder"])
        p7_species_increment = tuple(.5 * float(dt_s) * (
            r0["p7_species_rate"][j] + r1["p7_species_rate"][j]) for j in range(4))
        p7_heat_increment = .5 * float(dt_s) * (r0["p7_heat_rate"] + r1["p7_heat_rate"])
        p7_limited_increment = .5 * float(dt_s) * (
            limiter0["limited_reactant_rate_kg_s"] +
            limiter1["limited_reactant_rate_kg_s"])
        if step_p7_event is not None:
            step_p7_event.record(p7_species_increment, p7_heat_increment)
        self.p7_event = step_p7_event
        if archived_p7_event is not None:
            self.p7_events.append(archived_p7_event)
        self.p7_source_species_kg = [self.p7_source_species_kg[j] +
                                     p7_species_increment[j] for j in range(4)]
        self.p7_heat_added_j += p7_heat_increment
        self.ledger["p7_heat_added_J"] += p7_heat_increment
        self.ledger["p7_availability_limited_kg"] += p7_limited_increment
        self.ledger["p7_source_species_kg"] = list(self.p7_source_species_kg)
        trace = {"angle_start_deg": start_angle, "angle_end_deg": end_angle,
                 "time_start_s": self.time_s, "dt_s": float(dt_s),
                 "rpm": float(delta_angle_deg) / (6.0 * float(dt_s)),
                 "stage_states": (q0, q1, qn),
                 "stage_face_fluxes": (r0["faces"], r1["faces"]),
                 "stage_network_exchanges": (r0["network_exchanges"],
                                             r1["network_exchanges"]),
                 "stage_external": (r0["external"], r1["external"]),
                 "stage_cycle_rates": tuple({
                     "fresh_air_intake_delivery_kg_s": item[
                         "fresh_air_intake_delivered_rate"],
                     "fresh_delivery_kg_s": item["fresh_delivered_rate"],
                     "fresh_short_circuit_kg_s": item["fresh_short_circuit_rate"],
                     "fuel_delivery_kg_s": item["fuel_delivered_rate"],
                     "fuel_short_circuit_kg_s": item["fuel_short_circuited_rate"]}
                     for item in (r0, r1)),
                 "stage_geometry": (vars(r0["geometry"]), vars(r1["geometry"])),
                 "stage_work_rates": (r0["work_rates"], r1["work_rates"]),
                 "stage_thermal_rates": (wall_rates_0, wall_rates_1),
                 "stage_p7_source_rates": (
                     {"species_kg_s": r0["p7_species_rate"],
                      "heat_w": r0["p7_heat_rate"]},
                     {"species_kg_s": r1["p7_species_rate"],
                      "heat_w": r1["p7_heat_rate"]}),
                 "stage_p7_limiter": (limiter0, limiter1),
                 "p7_availability_limited_kg": p7_limited_increment,
                 "p7_source_species_increment_kg": p7_species_increment,
                 "p7_heat_increment_j": p7_heat_increment,
                 "heat_to_wall_J": heat_to_wall,
                 "stage_cfl": (cfl0, cfl1),
                 "inventory": self.inventory(qn), "dependency": self.dependency_status}
        self.state = qn
        self.crank_angle_unwrapped_deg = end_angle
        self.angle_deg = end_angle % 360.0
        self.time_s += float(dt_s)
        self.cycle = int(end_angle // 360.0)
        self.accepted_steps += 1
        self.trace.append(trace)
        return trace

    def conservation_report(self):
        final = self.inventory()
        delta_species = tuple(final["species_kg"][i]-self.initial_inventory["species_kg"][i]
                              for i in range(4))
        return {"mass": {"initial": self.initial_inventory["mass_kg"],
                          "final": final["mass_kg"],
                          "external": self.ledger["external_mass_kg"],
                          "residual": final["mass_kg"]-self.initial_inventory["mass_kg"]-
                                      self.ledger["external_mass_kg"]},
                "energy": {"initial": self.initial_inventory["energy_J"],
                           "final": final["energy_J"],
                           "external": self.ledger["external_energy_J"],
                           "work": self.ledger["crankcase_work_J"]+
                                   self.ledger["cylinder_work_J"],
                          "residual": final["energy_J"]-self.initial_inventory["energy_J"]-
                                      self.ledger["external_energy_J"]-
                                      self.ledger["p7_heat_added_J"]-
                                      self.ledger["crankcase_work_J"]-
                                       self.ledger["cylinder_work_J"]+
                                       self.ledger["heat_to_wall_J"]},
                "species": {SPECIES[i]: {"initial": self.initial_inventory["species_kg"][i],
                                         "final": final["species_kg"][i],
                                         "external": self.ledger["external_species_kg"][i],
                                         "source": self.ledger["p7_source_species_kg"][i],
                                         "residual": delta_species[i]-
                                                    self.ledger["external_species_kg"][i]-
                                                    self.ledger["p7_source_species_kg"][i]}
                            for i in range(4)}}

    def snapshot(self):
        self._assert_configuration_unchanged(check_identity=True)
        return {"schema": self.schema, "configuration_identity": deepcopy(self.configuration_identity),
                "state": _jsonify(self.state), "angle_deg": self.angle_deg,
                "crank_angle_unwrapped_deg": self.crank_angle_unwrapped_deg,
                "time_s": self.time_s, "cycle": self.cycle,
                "accepted_steps": self.accepted_steps,
                "rejected_steps": self.rejected_steps,
                "max_cfl": self.max_cfl,
                "ledger": _jsonify(self.ledger),
                "p7": {"active_event": (None if self.p7_event is None else
                                         snapshot_event(self.p7_event)),
                       "completed_events": deepcopy(self.p7_events)},
                "initial_inventory": _jsonify(self.initial_inventory),
                "trace": _jsonify(self.trace)}

    def restore(self, snapshot):
        self._assert_configuration_unchanged(check_identity=True)
        if not isinstance(snapshot, dict) or snapshot.get("schema") != self.schema:
            raise ValueError("integrated engine checkpoint schema mismatch")
        if snapshot.get("configuration_identity") != self.configuration_identity:
            raise ValueError("integrated engine checkpoint configuration mismatch")
        if snapshot.get("max_cfl") != self.max_cfl:
            raise ValueError("integrated engine checkpoint CFL configuration mismatch")
        state = _tuplify(deepcopy(snapshot.get("state")))
        self._validate(state)
        angle = snapshot.get("angle_deg")
        unwrapped = snapshot.get("crank_angle_unwrapped_deg")
        time_s = snapshot.get("time_s")
        counters = tuple(snapshot.get(name) for name in
                         ("cycle", "accepted_steps", "rejected_steps"))
        if (any(type(value) not in (int, float) or not isfinite(value)
                for value in (angle, unwrapped, time_s)) or time_s < 0 or
                not 0 <= angle < 360 or type(counters[0]) is not int or
                counters[0] != int(unwrapped // 360.0) or
                any(type(value) is not int or value < 0 for value in counters[1:])):
            raise ValueError("integrated engine checkpoint clock/counters are invalid")
        expected_angle = float(unwrapped) % 360.0
        if abs(float(angle) - expected_angle) > 1e-10:
            raise ValueError("integrated engine checkpoint wrapped/unwrapped angle mismatch")
        # The caller-supplied geometry identity binds the geometry definition;
        # also bind the actual restored state to that definition at its exact
        # checkpoint angle.  This catches stale-volume and mismatched-callback
        # checkpoints before mutating the live engine.
        restored_geometry = self._geometry(float(unwrapped))
        for chamber_name, expected_volume in (
                ("crankcase", restored_geometry.crankcase_volume_m3),
                ("cylinder", restored_geometry.cylinder_volume_m3)):
            actual_volume = state["chambers"][chamber_name][2]
            if actual_volume != expected_volume:
                raise ValueError(
                    f"integrated engine checkpoint {chamber_name} geometry mismatch")
        ledger = deepcopy(snapshot.get("ledger"))
        ledger_fields = {"external_mass_kg", "external_energy_J", "external_species_kg",
                         "fresh_delivered_kg", "fresh_short_circuit_kg", "fuel_delivered_kg",
                         "fuel_short_circuited_kg",
                         "heat_to_wall_J", "cylinder_work_J", "crankcase_work_J",
                         "p7_heat_added_J", "p7_availability_limited_kg",
                         "p7_source_species_kg"}
        if not isinstance(ledger, dict) or set(ledger) != ledger_fields:
            raise ValueError("integrated engine checkpoint ledger schema mismatch")
        if (not isinstance(ledger["external_species_kg"], (list, tuple)) or
                len(ledger["external_species_kg"]) != 4 or
                not isinstance(ledger["p7_source_species_kg"], (list, tuple)) or
                len(ledger["p7_source_species_kg"]) != 4 or
                any(type(value) not in (int, float) or not isfinite(value)
                    for key, value in ledger.items()
                    for value in (ledger[key] if key in
                                  {"external_species_kg", "p7_source_species_kg"} else
                                  (value,)))):
            raise ValueError("integrated engine checkpoint ledger contains invalid values")
        baseline = json.loads(json.dumps(self.initial_inventory, sort_keys=True))
        initial = json.loads(json.dumps(snapshot.get("initial_inventory"), sort_keys=True))
        if initial != baseline:
            raise ValueError("integrated engine checkpoint initial inventory mismatch")
        trace = snapshot.get("trace")
        if not isinstance(trace, list) or len(trace) != counters[1]:
            raise ValueError("integrated engine checkpoint primary trace is incomplete")
        p7 = snapshot.get("p7")
        if (not isinstance(p7, dict) or set(p7) != {"active_event", "completed_events"} or
                not isinstance(p7["completed_events"], list)):
            raise ValueError("integrated engine checkpoint P7 state is invalid")
        active_event = (None if p7["active_event"] is None else
                        _restore_validated_p7_event(p7["active_event"]))
        completed_events = [_restore_validated_p7_event(item)
                            for item in p7["completed_events"]]
        if (self.combustion_start_angle_deg is None and
                (active_event is not None or completed_events)):
            raise ValueError("integrated engine checkpoint has unconfigured P7 state")
        if active_event is not None and (
                abs((active_event.start % 360.0) - self.combustion_start_angle_deg) > 1e-10):
            raise ValueError("integrated engine checkpoint P7 event identity mismatch")
        if any(abs((event.start % 360.0) - self.combustion_start_angle_deg) > 1e-10
               for event in completed_events):
            raise ValueError("integrated engine checkpoint P7 history identity mismatch")
        if self.combustion_start_angle_deg is not None:
            phase = self.combustion_start_angle_deg
            latest_ignition = None
            if float(unwrapped) >= phase - 1e-10:
                latest_ignition = phase + 360.0 * max(
                    0, int((float(unwrapped) - phase) // 360.0))
            exact_ignition = (latest_ignition is not None and
                              abs(float(unwrapped) - latest_ignition) <= 1e-10)
            if latest_ignition is None:
                if active_event is not None or completed_events:
                    raise ValueError("integrated engine checkpoint has premature P7 history")
            else:
                allowed_active_starts = {latest_ignition}
                if exact_ignition and latest_ignition - 360.0 >= phase:
                    allowed_active_starts.add(latest_ignition - 360.0)
                if active_event is None:
                    first_ignition_pending = (exact_ignition and
                                              latest_ignition == phase and phase > 0.0)
                    if not first_ignition_pending:
                        raise ValueError(
                            "integrated engine checkpoint is missing the event for its crank-angle phase")
                    expected_completed = []
                else:
                    if not any(abs(active_event.start - value) <= 1e-10
                               for value in allowed_active_starts):
                        raise ValueError(
                            "integrated engine checkpoint P7 event cycle disagrees with unwrapped angle")
                    expected_completed = [
                        phase + 360.0 * cycle
                        for cycle in range(int((active_event.start - phase) // 360.0))]
                actual_completed = [event.start for event in completed_events]
                if (len(actual_completed) != len(expected_completed) or
                        any(abs(actual - expected) > 1e-10
                            for actual, expected in zip(actual_completed,
                                                       expected_completed))):
                    raise ValueError(
                        "integrated engine checkpoint P7 completed-event chronology is invalid")
        p7_all_events = completed_events + ([] if active_event is None else [active_event])
        p7_expected_species = (
            -fsum(event.ledger.fresh_air_converted for event in p7_all_events),
            -fsum(event.ledger.fuel_converted for event in p7_all_events),
            0.0,
            fsum(event.ledger.burned_produced for event in p7_all_events))
        if (any(not isclose(float(ledger["p7_source_species_kg"][j]),
                            p7_expected_species[j], rel_tol=1e-12, abs_tol=1e-12)
                for j in range(4)) or
                not isclose(float(ledger["p7_heat_added_J"]),
                            fsum(event.ledger.heat_added for event in p7_all_events),
                            rel_tol=1e-12, abs_tol=1e-12)):
            raise ValueError("integrated engine checkpoint P7 aggregate ledger is inconsistent")
        # Commit restored values only after the entire checkpoint passes validation.
        self.state = state
        self.angle_deg = float(angle)
        self.crank_angle_unwrapped_deg = float(unwrapped)
        self.time_s = float(time_s)
        self.cycle, self.accepted_steps, self.rejected_steps = counters
        self.ledger = ledger
        self.p7_event = active_event
        self.p7_events = [snapshot_event(item) for item in completed_events]
        self.p7_heat_added_j = float(ledger["p7_heat_added_J"])
        self.p7_source_species_kg = list(ledger["p7_source_species_kg"])
        self.initial_inventory = deepcopy(snapshot["initial_inventory"])
        self.trace = deepcopy(trace)


def _fresh_air_intake_rate(intake_duct_id: str, row: dict,
                           stage_index: int) -> float:
    """Read gross fresh-air intake from an explicit stage rate or its signed face flux.

    The fallback keeps earlier V2 primary traces readable; it uses the saved
    intake-boundary species flux, not a reconstructed or assumed mixture.
    """
    stage_rates = row.get("stage_cycle_rates", ())
    if len(stage_rates) != 2 or stage_index not in (0, 1):
        raise ValueError("integrated cycle intake stage-rate evidence is incomplete")
    direct = stage_rates[stage_index].get("fresh_air_intake_delivery_kg_s")
    faces = row.get("stage_face_fluxes", ())
    if len(faces) != 2 or intake_duct_id not in faces[stage_index]:
        raise ValueError("integrated cycle lacks signed intake donor flux")
    species = faces[stage_index][intake_duct_id].get("left_species")
    if (not isinstance(species, (list, tuple)) or len(species) != 4 or
            type(species[0]) not in (int, float) or not isfinite(species[0])):
        raise ValueError("integrated cycle signed intake species flux is invalid")
    from_face = max(0.0, float(species[0]))
    if direct is None:
        return from_face
    if (type(direct) not in (int, float) or not isfinite(direct) or direct < 0.0 or
            not isclose(float(direct), from_face, rel_tol=1e-12, abs_tol=1e-15)):
        raise ValueError("integrated cycle fresh-air intake rate differs from signed face flux")
    return float(direct)


def make_integrated_cycle_primary(engine: IntegratedEngine2T,
                                 start_checkpoint: dict,
                                 end_checkpoint: dict,
                                 cycle_index: int) -> dict:
    """Rebuild one complete 360-degree primary record from accepted stages.

    Checkpoint ledgers are cross-checks only. Cycle terms and periodic
    observables are recomputed from the saved stage trajectory.
    """
    if not isinstance(engine, IntegratedEngine2T):
        raise ValueError("integrated cycle evidence requires IntegratedEngine2T")
    if type(cycle_index) is not int or cycle_index < 1:
        raise ValueError("integrated cycle index must be a positive integer")
    for checkpoint in (start_checkpoint, end_checkpoint):
        if (not isinstance(checkpoint, dict) or checkpoint.get("schema") != engine.schema or
                checkpoint.get("configuration_identity") != engine.configuration_identity):
            raise ValueError("integrated cycle checkpoint identity mismatch")
    start_angle = float(cycle_index - 1) * 360.0
    end_angle = float(cycle_index) * 360.0
    if (start_checkpoint.get("crank_angle_unwrapped_deg") != start_angle or
            end_checkpoint.get("crank_angle_unwrapped_deg") != end_angle or
            end_checkpoint.get("cycle") != cycle_index):
        raise ValueError("integrated cycle checkpoints must bind exact 360-degree boundaries")
    start_index = start_checkpoint.get("accepted_steps")
    end_index = end_checkpoint.get("accepted_steps")
    if (type(start_index) is not int or type(end_index) is not int or
            start_index < 0 or end_index <= start_index):
        raise ValueError("integrated cycle accepted-step interval is invalid")
    trajectory = end_checkpoint.get("trace", [])[start_index:end_index]
    if len(trajectory) != end_index - start_index:
        raise ValueError("integrated cycle primary trajectory is incomplete")
    if (trajectory[0].get("angle_start_deg") != start_angle or
            trajectory[-1].get("angle_end_deg") != end_angle):
        raise ValueError("integrated cycle trajectory does not cover the exact cycle")
    prior_end = start_angle
    prior_state = start_checkpoint["state"]
    cfl_values = []
    external_mass = external_energy = p7_heat = wall_heat = 0.0
    p7_limited_mass = 0.0
    external_species = [0.0] * 4
    p7_species = [0.0] * 4
    rates_integral = {"fresh_air_intake_delivery_kg": 0.0,
                      "fresh_delivery_kg": 0.0,
                      "fresh_short_circuit_kg": 0.0,
                      "fuel_delivery_kg": 0.0,
                      "fuel_short_circuit_kg": 0.0,
                      "cylinder_work_J": 0.0,
                      "crankcase_work_J": 0.0}
    for row in trajectory:
        if (not isinstance(row, dict) or row.get("angle_start_deg") != prior_end or
                len(row.get("stage_states", ())) != 3 or
                len(row.get("stage_external", ())) != 2 or
                len(row.get("stage_cycle_rates", ())) != 2 or
                len(row.get("stage_p7_source_rates", ())) != 2 or
                len(row.get("stage_p7_limiter", ())) != 2 or
                len(row.get("stage_work_rates", ())) != 2 or
                len(row.get("stage_thermal_rates", ())) != 2 or
                len(row.get("stage_cfl", ())) != 2):
            raise ValueError("integrated cycle stage trajectory is incomplete or discontinuous")
        if json.dumps(row["stage_states"][0], sort_keys=True) != json.dumps(
                prior_state, sort_keys=True):
            raise ValueError("integrated cycle stage state does not continue prior state")
        dt = row.get("dt_s")
        if type(dt) not in (int, float) or not isfinite(dt) or dt <= 0:
            raise ValueError("integrated cycle timestep is invalid")
        for stage_state in row["stage_states"]:
            engine._validate(_tuplify(stage_state))
        cfl_values.extend(row["stage_cfl"])
        if any(type(value) not in (int, float) or not isfinite(value) or
               value < 0 or value > engine.max_cfl for value in row["stage_cfl"]):
            raise ValueError("integrated cycle contains an inadmissible CFL value")
        external0, external1 = row["stage_external"]
        external_mass += .5 * dt * (external0["mass"] + external1["mass"])
        external_energy += .5 * dt * (external0["energy"] + external1["energy"])
        for index in range(4):
            external_species[index] += .5 * dt * (
                external0["species"][index] + external1["species"][index])
            p7_species[index] += .5 * dt * (
                row["stage_p7_source_rates"][0]["species_kg_s"][index] +
                row["stage_p7_source_rates"][1]["species_kg_s"][index])
        p7_heat += .5 * dt * sum(
            stage["heat_w"] for stage in row["stage_p7_source_rates"])
        p7_limited_mass += .5 * dt * sum(
            stage["limited_reactant_rate_kg_s"]
            for stage in row["stage_p7_limiter"])
        wall_heat += .5 * dt * sum(
            sum(stage.values()) for stage in row["stage_thermal_rates"])
        for rate_name, trace_name in (
                ("fresh_delivery_kg", "fresh_delivery_kg_s"),
                ("fresh_short_circuit_kg", "fresh_short_circuit_kg_s"),
                ("fuel_delivery_kg", "fuel_delivery_kg_s"),
                ("fuel_short_circuit_kg", "fuel_short_circuit_kg_s")):
            rates_integral[rate_name] += .5 * dt * sum(
                stage[trace_name] for stage in row["stage_cycle_rates"])
        rates_integral["fresh_air_intake_delivery_kg"] += .5 * dt * sum(
            _fresh_air_intake_rate(engine.intake.id, row, stage_index)
            for stage_index in range(2))
        for name in ("cylinder", "crankcase"):
            rates_integral[f"{name}_work_J"] += .5 * dt * sum(
                stage[name] for stage in row["stage_work_rates"])
        prior_end = row["angle_end_deg"]
        prior_state = row["stage_states"][2]
    if json.dumps(prior_state, sort_keys=True) != json.dumps(
            end_checkpoint["state"], sort_keys=True):
        raise ValueError("integrated cycle terminal stage state mismatch")

    start_state = _tuplify(start_checkpoint["state"])
    end_state = _tuplify(end_checkpoint["state"])
    start_inventory = engine.inventory(start_state)
    end_inventory = engine.inventory(end_state)
    end_ledger = end_checkpoint["ledger"]
    start_ledger = start_checkpoint["ledger"]
    recomputed = {
        "external_mass_kg": external_mass,
        "external_energy_J": external_energy,
        "external_species_kg": external_species,
        "fresh_delivered_kg": rates_integral["fresh_delivery_kg"],
        "fresh_short_circuit_kg": rates_integral["fresh_short_circuit_kg"],
        "fuel_delivered_kg": rates_integral["fuel_delivery_kg"],
        "fuel_short_circuited_kg": rates_integral["fuel_short_circuit_kg"],
        "heat_to_wall_J": wall_heat,
        "cylinder_work_J": rates_integral["cylinder_work_J"],
        "crankcase_work_J": rates_integral["crankcase_work_J"],
        "p7_heat_added_J": p7_heat,
        "p7_availability_limited_kg": p7_limited_mass,
        "p7_source_species_kg": p7_species,
    }
    for key, value in recomputed.items():
        expected = [end_ledger[key][i] - start_ledger[key][i]
                    for i in range(4)] if key in {
                        "external_species_kg", "p7_source_species_kg"} else (
                            value if key not in end_ledger else end_ledger[key] - start_ledger[key])
        if isinstance(value, list):
            if any(not isclose(value[i], expected[i], rel_tol=1e-10, abs_tol=1e-14)
                   for i in range(4)):
                raise ValueError(f"integrated cycle ledger differs from primary {key}")
        elif not isclose(value, expected, rel_tol=1e-10, abs_tol=1e-14):
            raise ValueError(f"integrated cycle ledger differs from primary {key}")

    def chamber_observables(state, name):
        mass, energy, volume = state["chambers"][name]
        pressure = (engine.eos.gamma - 1.0) * energy / volume
        return {"mass_kg": mass, "total_energy_J": energy,
                "pressure_Pa": pressure, "temperature_K": energy / (mass * engine.eos.cv)}

    ducts = {}
    for path in engine.ducts:
        cells = []
        for q, composition, volume in zip(
                end_state["ducts"][path.id],
                end_state["species"]["ducts"][path.id], path.mesh.volumes):
            rho, momentum, energy_density, _ = q
            velocity = momentum / rho
            pressure = (engine.eos.gamma - 1.0) * (
                energy_density - .5 * momentum * momentum / rho)
            total_mass = sum(composition)
            sound = engine.eos.sound_speed((rho, velocity, pressure, 1.0))
            cells.append({"mass_kg": rho * volume,
                          "total_energy_J": energy_density * volume,
                          "pressure_Pa": pressure,
                          "temperature_K": pressure / (rho * engine.eos.R),
                          "species_mass_fractions": [value / total_mass
                                                     for value in composition],
                          "velocity_over_sound_speed": velocity / sound})
        ducts[path.id] = cells
    port_closures = {"status": "UNAVAILABLE", "reason": None, "snapshots": {}}
    if engine.port_binding is None:
        port_closures["reason"] = "No generic port geometry is bound to this cycle."
    else:
        rpm_values = [float(row["rpm"]) for row in trajectory]
        cycle_rpm = rpm_values[0]
        if any(not isclose(value, cycle_rpm, rel_tol=1e-12, abs_tol=1e-9)
               for value in rpm_values[1:]):
            port_closures["reason"] = (
                "Exact powervalve closure angles require a constant-RPM cycle; "
                "no interpolation is used for variable-RPM trajectories.")
        else:
            binding = engine.port_binding
            ports = binding.port_set
            if binding.powervalve is not None:
                valve = binding.powervalve
                ports = replace(ports, ports=tuple(
                    valve.apply(port, cycle_rpm) if port.id == valve.exhaust_port_id else port
                    for port in ports.ports))
            path_roles = {path.id: path.role for path in engine.ducts}
            closures_by_role = {}
            for duct in ports.ducts:
                path_id = binding.path_by_duct[duct.id]
                role = path_roles[path_id]
                if role not in {"transfer", "exhaust"}:
                    continue
                for base_angle in ports.duct_closing_angles(duct.id):
                    target = start_angle + ((base_angle - start_angle) % 360.0)
                    if target <= start_angle + 1e-9:
                        target += 360.0
                    if target <= end_angle + 1e-9:
                        closures_by_role.setdefault(role, []).append((target, duct.id))
            for role in ("transfer", "exhaust"):
                candidates = closures_by_role.get(role, [])
                if not candidates:
                    port_closures["reason"] = f"No exact {role} closure occurs in this cycle."
                    break
                target = max(angle for angle, _ in candidates)
                closure_ducts = sorted(duct_id for angle, duct_id in candidates
                                       if isclose(angle, target, rel_tol=0.0, abs_tol=1e-9))
                matches = [row for row in trajectory
                           if isclose(float(row["angle_end_deg"]), target,
                                      rel_tol=0.0, abs_tol=1e-9)]
                if len(matches) != 1:
                    port_closures["reason"] = (
                        f"Accepted trajectory lacks one exact {role} closure state at "
                        f"{target:.12g} degrees.")
                    break
                state = _tuplify(matches[0]["stage_states"][2])
                chamber_species = list(state["species"]["chambers"]["cylinder"])
                port_closures["snapshots"][role] = {
                    "angle_deg": target, "duct_ids": closure_ducts,
                    "species_order": list(SPECIES),
                    "cylinder_species_kg": chamber_species,
                    "cylinder_total_mass_kg": sum(chamber_species),
                    "state_source": "accepted SSPRK2 terminal stage at exact geometry event"}
            if len(port_closures["snapshots"]) == 2:
                port_closures["status"] = "EXACT_EVENT_STATES_CAPTURED"
                port_closures["reason"] = None
    observables = {"chambers": {name: chamber_observables(end_state, name)
                                for name in ("cylinder", "crankcase")},
                   "ducts": ducts,
                   "global_species_kg": list(end_inventory["species_kg"]),
                   "cylinder_species_kg": list(
                       end_state["species"]["chambers"]["cylinder"]),
                   "cycle_start_total_mass_kg": start_inventory["mass_kg"],
                   "cycle_start_total_energy_J": start_inventory["energy_J"],
                   # The stage RHS ledger is gas-energy transfer (-p dV/dt).
                   # Indicated work produced by the cylinder is its negative.
                   "work_J": -rates_integral["cylinder_work_J"],
                   "cylinder_energy_work_J": rates_integral["cylinder_work_J"],
                   "fresh_delivery_kg": rates_integral["fresh_delivery_kg"],
                   "fresh_short_circuit_kg": rates_integral["fresh_short_circuit_kg"],
                   "fresh_air_intake_delivery_kg": rates_integral[
                       "fresh_air_intake_delivery_kg"],
                   "fuel_delivered_kg": rates_integral["fuel_delivery_kg"],
                   "fuel_short_circuited_kg": rates_integral[
                       "fuel_short_circuit_kg"],
                   "p7_fuel_consumed_kg": -p7_species[1],
                   "fuel_unburned_terminal_global_kg": end_inventory["species_kg"][1],
                   "fuel_inventory_start_global_kg": start_inventory["species_kg"][1],
                   "fuel_external_net_kg": external_species[1],
                   "fuel_mass_balance_residual_kg": (
                       end_inventory["species_kg"][1] -
                       start_inventory["species_kg"][1] - external_species[1] -
                       p7_species[1]),
                   "p7_burned_produced_kg": p7_species[3],
                   "p7_heat_J": p7_heat}
    mass_residual = end_inventory["mass_kg"] - start_inventory["mass_kg"] - external_mass
    energy_residual = (end_inventory["energy_J"] - start_inventory["energy_J"] -
                       external_energy - p7_heat - rates_integral["cylinder_work_J"] -
                       rates_integral["crankcase_work_J"] + wall_heat)
    species_residual = [end_inventory["species_kg"][i] -
                        start_inventory["species_kg"][i] - external_species[i] -
                        p7_species[i] for i in range(4)]
    terminal_rpm = float(trajectory[-1]["rpm"])
    p7_state = end_checkpoint.get("p7", {})
    if not isinstance(p7_state, dict):
        raise ValueError("integrated cycle terminal checkpoint lacks P7 state")
    terminal_event = (_restore_validated_p7_event(p7_state["active_event"])
                      if p7_state.get("active_event") is not None else None)
    terminal_rhs = engine._assemble(end_state, end_angle, terminal_rpm, terminal_event)
    terminal_diagnostic = {
        "state_source": "accepted terminal state; read-only instantaneous RHS evaluation",
        "geometry": vars(terminal_rhs["geometry"]),
        "face_fluxes": terminal_rhs["faces"],
        "p7_heat_requested_W": terminal_rhs["p7_heat_rate"],
        "thermal_rates_W": terminal_rhs["thermal_rates"],
        "p7_rate_semantics": "instantaneous prescribed rate before any future-step availability limiter"}
    return {"schema": "MOTORSIM_INTEGRATED_2T_CYCLE_PRIMARY_V2",
            "contract": "REFERENCE_PERIODIC_CONVERGENCE_V1",
            "cycle_index": cycle_index,
            "configuration_hash": engine.configuration_identity["configuration_sha256"],
            "eos_R": engine.eos.R, "eos_gamma": engine.eos.gamma,
            "eos_cv": engine.eos.cv,
            "duct_roles": {path.id: path.role for path in engine.ducts},
            "port_closure_geometry": (None if engine.port_binding is None else
                                       engine.port_binding.to_dict()),
            "port_closure_snapshots": port_closures,
            "cycle_start_deg": start_angle, "cycle_end_deg": end_angle,
            "start_state": _jsonify(start_state),
            "terminal_state": _jsonify(end_state),
            "duct_volumes_m3": {path.id: list(path.mesh.volumes)
                                for path in engine.ducts},
            "network_volume_definitions": {
                binding.node.id: {"kind": binding.node.kind,
                                  "volume_m3": binding.node.volume_m3}
                for binding in engine.network_volumes},
            "trajectory": deepcopy(trajectory),
            "terminal_diagnostic": _jsonify(terminal_diagnostic),
            "observables": observables,
            "cycle_ledgers": recomputed,
            "conservation": {"mass_residual_kg": mass_residual,
                             "energy_residual_J": energy_residual,
                             "species_residual_kg": species_residual},
            "CFL": {"min": min(cfl_values), "max": max(cfl_values)},
            "P7_availability_limited_kg": p7_limited_mass,
            "admissible": True,
            "evidence_source": "accepted IntegratedEngine2T SSPRK2 stage trajectory"}


def _specific_consumption_value(fuel_consumed_kg: float, duration_s: float,
                                power_w: float) -> float | None:
    """Return g/kWh only for positive prescribed consumed fuel and output power."""
    if (not all(isfinite(value) for value in
                (fuel_consumed_kg, duration_s, power_w)) or
            fuel_consumed_kg <= 0.0 or duration_s <= 0.0 or power_w <= 0.0):
        return None
    return fuel_consumed_kg / duration_s * 3.6e9 / power_w


def make_integrated_engineering_output(cycle_record: dict, *,
                                       displacement_m3: float,
                                       mechanical_loss_model=None,
                                       load: float = 0.0,
                                       scavenging_reference_mass_kg: float | None = None) -> dict:
    """Build the existing engineering-output schema from one primary cycle.

    Only quantities present in the accepted trajectory or explicitly supplied
    through the existing mechanical model are defined.  Fuel properties and
    exact port-closure states are intentionally not inferred here.
    """
    from .engineering_outputs import build_integrated_engineering_output_v3

    if (not isinstance(cycle_record, dict) or
            cycle_record.get("schema") != "MOTORSIM_INTEGRATED_2T_CYCLE_PRIMARY_V2" or
            cycle_record.get("contract") != "REFERENCE_PERIODIC_CONVERGENCE_V1" or
            cycle_record.get("admissible") is not True):
        raise ValueError("engineering output requires admissible integrated cycle evidence")
    trajectory = cycle_record.get("trajectory")
    if not isinstance(trajectory, list) or not trajectory:
        raise ValueError("engineering output requires a complete accepted trajectory")
    network_volume_definitions = cycle_record.get("network_volume_definitions", {})
    if not isinstance(network_volume_definitions, dict):
        raise ValueError("engineering output network volume definitions are invalid")
    for node_id, definition in network_volume_definitions.items():
        if (not isinstance(node_id, str) or not node_id.strip() or
                not isinstance(definition, dict) or
                set(definition) != {"kind", "volume_m3"} or
                definition["kind"] not in VOLUME_KINDS or
                type(definition["volume_m3"]) not in (int, float) or
                not isfinite(definition["volume_m3"]) or
                definition["volume_m3"] <= 0.0):
            raise ValueError("engineering output network volume definition is malformed")
    start = cycle_record.get("cycle_start_deg")
    end = cycle_record.get("cycle_end_deg")
    if (type(start) not in (int, float) or type(end) not in (int, float) or
            not isclose(end - start, 360.0, rel_tol=0.0, abs_tol=1e-10)):
        raise ValueError("engineering output requires one complete 360-degree cycle")
    displacement = float(displacement_m3)
    if not isfinite(displacement) or displacement <= 0.0:
        raise ValueError("engineering output requires positive displacement")
    duct_roles = cycle_record.get("duct_roles")
    if (not isinstance(duct_roles, dict) or
            set(duct_roles) != set(cycle_record.get("duct_volumes_m3", {}))):
        raise ValueError("cycle primary record lacks stable duct role identity")
    role_ids = _duct_ids_by_role(duct_roles)
    intake_duct_id = role_ids["intake"][0]

    def sample(state, geometry, face_fluxes):
        values = {}
        for name in ("cylinder", "crankcase"):
            mass, energy, volume = state["chambers"][name]
            gamma = float(cycle_record["eos_gamma"])
            values[f"{name}_mass_kg"] = mass
            values[f"{name}_temperature_k"] = energy / (mass * float(cycle_record["eos_cv"]))
            values[f"{name}_pressure_pa"] = (gamma - 1.0) * energy / volume
            values[f"{name}_volume_m3"] = volume
        for index, name in enumerate(SPECIES):
            values[f"{name}_mass_kg"] = state["species"]["chambers"]["cylinder"][index]
        values["transfer_port_area_m2"] = sum(geometry["transfer_areas_m2"])
        values["exhaust_port_area_m2"] = geometry["exhaust_area_m2"]
        values.update(_role_face_outputs(face_fluxes, role_ids))

        gamma = float(cycle_record["eos_gamma"])
        gas_constant = float(cycle_record["eos_R"])
        for duct_id, role in cycle_record["duct_roles"].items():
            encoded_id = quote(duct_id, safe="")
            for cell_index, (q, composition) in enumerate(zip(
                    state["ducts"][duct_id], state["species"]["ducts"][duct_id])):
                rho, momentum, energy_density, _ = q
                velocity = momentum / rho
                pressure = (gamma - 1.0) * (
                    energy_density - .5 * momentum * momentum / rho)
                temperature = pressure / (rho * gas_constant)
                sound = (gamma * pressure / rho) ** .5
                prefix = f"duct:{encoded_id}:cell:{cell_index}:"
                for field, value in (("pressure_pa", pressure),
                                     ("temperature_k", temperature),
                                     ("mach", velocity / sound)):
                    values[prefix + field] = value
                for index, species_name in enumerate(SPECIES):
                    values[prefix + f"{species_name}_mass_kg"] = composition[index]
            for face_index, face in enumerate(face_fluxes[duct_id]["all_faces"]):
                values[f"duct:{encoded_id}:face:{face_index}:mass_flow_kg_s"] = face[0]
        for node_id, definition in network_volume_definitions.items():
            if node_id not in state.get("network_volumes", {}):
                raise ValueError("cycle primary network volume state is missing")
            mass, energy, volume = state["network_volumes"][node_id]
            composition = state["species"]["network_volumes"][node_id]
            encoded_id = quote(node_id, safe="")
            prefix = f"network:{encoded_id}:"
            pressure = (gamma - 1.0) * energy / volume
            values[prefix + "mass_kg"] = mass
            values[prefix + "pressure_pa"] = pressure
            values[prefix + "temperature_k"] = energy / (mass * float(cycle_record["eos_cv"]))
            for index, species_name in enumerate(SPECIES):
                values[prefix + f"{species_name}_mass_kg"] = composition[index]
        return values

    # Bind thermodynamic constants into the primary record rather than relying
    # on whichever engine object happens to be present when a file is replayed.
    if (type(cycle_record.get("eos_gamma")) not in (int, float) or
            type(cycle_record.get("eos_R")) not in (int, float) or
            type(cycle_record.get("eos_cv")) not in (int, float)):
        raise ValueError("cycle primary record lacks EOS identity for output reconstruction")
    rows = []
    for accepted_row in trajectory:
        rows.append((float(accepted_row["angle_start_deg"]),
                     sample(_tuplify(accepted_row["stage_states"][0]),
                            accepted_row["stage_geometry"][0],
                            accepted_row["stage_face_fluxes"][0]),
                     accepted_row["stage_p7_source_rates"][0]["heat_w"],
                     sum(accepted_row["stage_thermal_rates"][0].values())))
    terminal = cycle_record.get("terminal_diagnostic")
    if not isinstance(terminal, dict) or terminal.get("state_source") != (
            "accepted terminal state; read-only instantaneous RHS evaluation"):
        raise ValueError("engineering output lacks its state-aligned terminal diagnostic")
    rows.append((float(end), sample(_tuplify(cycle_record["terminal_state"]),
                                    terminal["geometry"], terminal["face_fluxes"]),
                 float(terminal["p7_heat_requested_W"]),
                 sum(terminal["thermal_rates_W"].values())))
    duration = 0.0
    integrals = {name: 0.0 for name in (
        "cylinder_energy_work_J", "fresh_air_intake_delivery_kg",
        "fuel_delivery_kg", "fresh_delivery_kg",
        "fresh_short_circuit_kg", "fuel_short_circuit_kg",
        "wall_heat_loss_J", "p7_heat_J",
        "crankcase_energy_work_J")}
    external_mass = external_energy = 0.0
    external_species = [0.0] * 4
    p7_species = [0.0] * 4
    for row in trajectory:
        dt = float(row["dt_s"])
        duration += dt
        if (len(row.get("stage_work_rates", ())) != 2 or
                len(row.get("stage_cycle_rates", ())) != 2 or
                len(row.get("stage_external", ())) != 2 or
                len(row.get("stage_p7_source_rates", ())) != 2 or
                len(row.get("stage_thermal_rates", ())) != 2):
            raise ValueError("engineering output stage trajectory is incomplete")
        integrals["cylinder_energy_work_J"] += .5 * dt * sum(
            stage["cylinder"] for stage in row["stage_work_rates"])
        integrals["crankcase_energy_work_J"] += .5 * dt * sum(
            stage["crankcase"] for stage in row["stage_work_rates"])
        for target, source in (("fuel_delivery_kg", "fuel_delivery_kg_s"),
                               ("fresh_delivery_kg", "fresh_delivery_kg_s"),
                               ("fresh_short_circuit_kg", "fresh_short_circuit_kg_s"),
                               ("fuel_short_circuit_kg", "fuel_short_circuit_kg_s")):
            integrals[target] += .5 * dt * sum(
                stage[source] for stage in row["stage_cycle_rates"])
        integrals["fresh_air_intake_delivery_kg"] += .5 * dt * sum(
            _fresh_air_intake_rate(intake_duct_id, row, stage_index)
            for stage_index in range(2))
        integrals["wall_heat_loss_J"] += .5 * dt * sum(
            sum(stage.values()) for stage in row["stage_thermal_rates"])
        integrals["p7_heat_J"] += .5 * dt * sum(
            stage["heat_w"] for stage in row["stage_p7_source_rates"])
        for stage in row["stage_external"]:
            external_mass += .5 * dt * stage["mass"]
            external_energy += .5 * dt * stage["energy"]
            for i, value in enumerate(stage["species"]):
                external_species[i] += .5 * dt * value
        for stage in row["stage_p7_source_rates"]:
            for i, value in enumerate(stage["species_kg_s"]):
                p7_species[i] += .5 * dt * value
    if (not isclose(rows[-1][0], float(end), rel_tol=0.0, abs_tol=1e-10) or
            any(b[0] <= a[0] for a, b in zip(rows, rows[1:]))):
        raise ValueError("cycle trajectory does not supply ordered full-cycle output samples")
    rpm = 60.0 / duration
    cycle_number = cycle_record.get("cycle_index")
    obs = cycle_record.get("observables")
    ledgers = cycle_record.get("cycle_ledgers")
    if not isinstance(obs, dict) or not isinstance(ledgers, dict):
        raise ValueError("engineering output requires cycle-primary derived observables and ledgers")
    work = -integrals["cylinder_energy_work_J"]
    ledger_checks = {
        "external_mass_kg": external_mass,
        "external_energy_J": external_energy,
        "fuel_delivered_kg": integrals["fuel_delivery_kg"],
        "fuel_short_circuited_kg": integrals["fuel_short_circuit_kg"],
        "fresh_delivered_kg": integrals["fresh_delivery_kg"],
        "fresh_short_circuit_kg": integrals["fresh_short_circuit_kg"],
        "heat_to_wall_J": integrals["wall_heat_loss_J"],
        "cylinder_work_J": integrals["cylinder_energy_work_J"],
        "crankcase_work_J": integrals["crankcase_energy_work_J"],
        "p7_heat_added_J": integrals["p7_heat_J"],
    }
    for key, actual in ledger_checks.items():
        if not isclose(float(ledgers[key]), actual, rel_tol=1e-10, abs_tol=1e-14):
            raise ValueError(f"cycle primary ledger {key} differs from accepted stages")
    for key, actual in (("external_species_kg", external_species),
                        ("p7_source_species_kg", p7_species)):
        if (len(ledgers[key]) != 4 or any(not isclose(float(ledgers[key][i]), actual[i],
                rel_tol=1e-10, abs_tol=1e-14) for i in range(4))):
            raise ValueError(f"cycle primary ledger {key} differs from accepted stages")

    def inventory(state):
        volumes = cycle_record.get("duct_volumes_m3")
        if not isinstance(volumes, dict) or set(volumes) != set(state["ducts"]):
            raise ValueError("cycle primary duct volume identity is missing")
        mass = energy = 0.0
        species = [0.0] * 4
        for name in ("crankcase", "cylinder"):
            chamber_mass, chamber_energy, _ = state["chambers"][name]
            mass += chamber_mass
            energy += chamber_energy
            for i, value in enumerate(state["species"]["chambers"][name]):
                species[i] += value
        for duct, cells in state["ducts"].items():
            duct_volumes = volumes[duct]
            duct_species = state["species"]["ducts"][duct]
            if len(cells) != len(duct_volumes) or len(cells) != len(duct_species):
                raise ValueError("cycle primary duct inventory shape mismatch")
            for q, composition, volume in zip(cells, duct_species, duct_volumes):
                mass += q[0] * volume
                energy += q[2] * volume
                for i, value in enumerate(composition):
                    species[i] += value
        volume_definitions = network_volume_definitions
        network_volumes = state.get("network_volumes", {})
        network_species = state.get("species", {}).get("network_volumes", {})
        if (not isinstance(volume_definitions, dict) or
                set(volume_definitions) != set(network_volumes) or
                set(network_species) != set(network_volumes)):
            raise ValueError("cycle primary network volume identity is missing")
        for node_id, row in network_volumes.items():
            if (not isinstance(row, (tuple, list)) or len(row) != 3 or
                    any(type(value) not in (int, float) or not isfinite(value)
                        for value in row) or min(row[:2]) <= 0.0 or
                    row[2] != volume_definitions[node_id]["volume_m3"]):
                raise ValueError("cycle primary network volume geometry mismatch")
            mass += row[0]
            energy += row[1]
            composition = network_species[node_id]
            if not isinstance(composition, (tuple, list)) or len(composition) != 4:
                raise ValueError("cycle primary network species shape mismatch")
            composition = validate_species(composition, row[0])
            for i, value in enumerate(composition):
                species[i] += value
        return mass, energy, species

    initial_inventory = inventory(_tuplify(cycle_record["start_state"]))
    terminal_inventory = inventory(_tuplify(cycle_record["terminal_state"]))
    mass_residual = terminal_inventory[0] - initial_inventory[0] - external_mass
    energy_residual = (terminal_inventory[1] - initial_inventory[1] - external_energy -
                       integrals["p7_heat_J"] - integrals["cylinder_energy_work_J"] -
                       integrals["crankcase_energy_work_J"] + integrals["wall_heat_loss_J"])
    species_residual = [terminal_inventory[2][i] - initial_inventory[2][i] -
                        external_species[i] - p7_species[i] for i in range(4)]
    trace_recomputable = {
        "fresh_air_intake_delivery_kg", "fuel_delivered_kg",
        "fuel_short_circuited_kg", "p7_fuel_consumed_kg",
        "fuel_unburned_terminal_global_kg", "fuel_external_net_kg",
        "fuel_mass_balance_residual_kg"}
    for key, actual in (("work_J", work),
                        ("fresh_delivery_kg", integrals["fresh_delivery_kg"]),
                        ("fresh_short_circuit_kg", integrals["fresh_short_circuit_kg"]),
                        ("fresh_air_intake_delivery_kg",
                         integrals["fresh_air_intake_delivery_kg"]),
                        ("fuel_delivered_kg", integrals["fuel_delivery_kg"]),
                        ("fuel_short_circuited_kg", integrals["fuel_short_circuit_kg"]),
                        ("p7_fuel_consumed_kg", -p7_species[1]),
                        ("fuel_unburned_terminal_global_kg", terminal_inventory[2][1]),
                        ("fuel_external_net_kg", external_species[1]),
                        ("fuel_mass_balance_residual_kg", species_residual[1])):
        if key not in obs and key in trace_recomputable:
            continue
        if key not in obs:
            raise ValueError(f"cycle primary observable {key} is missing")
        if not isclose(float(obs[key]), actual, rel_tol=1e-10, abs_tol=1e-14):
            raise ValueError(f"cycle primary observable {key} differs from accepted stages")
    calculated_conservation = cycle_record.get("conservation", {})
    if (not isclose(float(calculated_conservation.get("mass_residual_kg")),
                    mass_residual, rel_tol=1e-10, abs_tol=1e-14) or
            not isclose(float(calculated_conservation.get("energy_residual_J")),
                        energy_residual, rel_tol=1e-10, abs_tol=1e-12) or
            any(not isclose(float(calculated_conservation.get("species_residual_kg")[i]),
                            species_residual[i], rel_tol=1e-10, abs_tol=1e-14)
                for i in range(4))):
        raise ValueError("cycle primary conservation summary differs from accepted stages")
    channels = {}
    for key in rows[0][1]:
        channels[key] = {
            "values": [row[1][key] for row in rows],
            "source": f"accepted integrated cycle stages; config {cycle_record['configuration_hash']}"}
    channels["heat_release_w"] = {
        "values": [row[2] for row in rows],
        "source": ("accepted SSPRK2 stage-start source; terminal point is a read-only "
                   "instantaneous prescribed rate before future-step availability limiting; "
                   f"config {cycle_record['configuration_hash']}")}
    channels["wall_heat_transfer_w"] = {
        "values": [row[3] for row in rows],
        "source": ("accepted SSPRK2 stage-start source and read-only terminal-state "
                   f"evaluation; config {cycle_record['configuration_hash']}")}

    metrics = {}
    def defined(name, value, source):
        metrics[name] = {"value": value, "status": "DEFINED", "reason": None,
                         "source": source}
    def undefined(name, reason):
        metrics[name] = {"value": None, "status": "UNDEFINED", "reason": reason,
                         "source": "integrated cycle evidence; required inputs unavailable"}

    defined("indicated_work_j", work, "accepted SSPRK2 cylinder pressure-volume integral ∮p dV")
    defined("indicated_power_w", work * rpm / 60.0,
            "indicated work times one 2T cycle per revolution")
    defined("indicated_torque_nm", work / (2.0 * pi),
            "indicated work divided by 2 pi")
    defined("imep_pa", work / displacement, "indicated work / explicit displacement")
    pressure_samples = [row[1]["cylinder_pressure_pa"] for row in rows]
    peak_index = max(range(len(pressure_samples)), key=pressure_samples.__getitem__)
    defined("peak_pressure_pa", pressure_samples[peak_index],
            "accepted integrated cylinder state samples")
    defined("angle_of_peak_pressure_deg", rows[peak_index][0] - float(start),
            "accepted integrated crank-angle samples relative to cycle start")
    defined("gross_fresh_charge_delivery_kg", integrals["fresh_delivery_kg"],
            "Gross sum of fresh_air + fuel species crossing transfer outlets into the cylinder; "
            "re-crossings are counted and mass is not deduplicated")
    defined("gross_fresh_charge_short_circuit_kg", integrals["fresh_short_circuit_kg"],
            "Gross outward fresh_air + fuel species crossing the exhaust while transfer and "
            "exhaust areas are open; reverse exhaust flow is excluded")
    defined("fuel_flow_kg_s",
            integrals["fuel_delivery_kg"] / duration,
            "Gross integrated P6 fuel-species inflow at the engine intake boundary / cycle duration")
    defined("fuel_delivered_per_cycle_kg", integrals["fuel_delivery_kg"],
            "accepted P6 fuel-species donor flow into the engine intake boundary")
    defined("fresh_air_intake_delivered_per_cycle_kg",
            integrals["fresh_air_intake_delivery_kg"],
            "accepted P6 fresh_air donor flow into the engine intake boundary")
    defined("fuel_short_circuited_per_cycle_kg", integrals["fuel_short_circuit_kg"],
            "accepted fuel-species flow leaving exhaust while transfer and exhaust are open")
    defined("fuel_consumed_by_p7_per_cycle_kg", -p7_species[1],
            "negative accepted P7 fuel-species source ledger; prescribed bookkeeping conversion")
    defined("fuel_unburned_terminal_global_kg", terminal_inventory[2][1],
            "terminal four-species inventory summed across cylinder, crankcase and ducts")
    undefined("cylinder_fuel_species_at_exhaust_close_kg",
              "An exact cylinder species snapshot at exhaust closure is unavailable.")
    defined("fuel_species_balance_residual_kg", species_residual[1],
            "independent global fuel-species balance from accepted trajectory")
    intake_fuel = integrals["fuel_delivery_kg"]
    if intake_fuel > 0.0:
        defined("gross_intake_air_fuel_ratio",
                integrals["fresh_air_intake_delivery_kg"] / intake_fuel,
                "Gross fresh_air / fuel species crossing the engine intake boundary; "
                "an intake charge ratio, not trapped or burned AFR")
    else:
        undefined("gross_intake_air_fuel_ratio",
                  "No positive fuel-species delivery at the intake boundary.")
    undefined("afr", "Trapped or burned air/fuel ratio is unavailable; this output only "
              "contains gross intake species delivery and prescribed P7 conversion.")
    undefined("equivalence_ratio", "Stoichiometric AFR is not configured for this fuel.")
    indicated_power = work * rpm / 60.0
    p7_fuel_consumption = -p7_species[1]
    defined("p7_fuel_consumption_flow_kg_s", p7_fuel_consumption / duration,
            "P7 prescribed fuel pseudo-species sink / cycle duration; not measured fuel burn")

    def specific_consumption(power_w: float, metric: str) -> None:
        value = _specific_consumption_value(p7_fuel_consumption, duration, power_w)
        if value is None:
            if power_w <= 0.0:
                undefined(metric, "The corresponding indicated/brake power is nonpositive.")
            elif p7_fuel_consumption <= 0.0:
                undefined(metric, "No positive P7 fuel pseudo-species consumption is recorded.")
            else:
                undefined(metric, "Fuel mass, cycle duration, or power is invalid.")
        else:
            defined(metric, value,
                    "P7 prescribed fuel pseudo-species consumption / positive power; "
                    "no LHV or experimental burn claim")

    specific_consumption(indicated_power, "isfc_g_kwh")
    defined("wall_heat_loss_j", integrals["wall_heat_loss_J"],
            "accepted SSPRK2 thermal source integral")
    defined("energy_balance_residual_j", energy_residual,
            "independent global energy balance from accepted trajectory and inventory")
    brake_power = None
    if mechanical_loss_model is None:
        for name in ("brake_work_j", "brake_power_w", "brake_torque_nm", "bmep_pa", "fmep_pa"):
            undefined(name, "No mechanical-loss model was explicitly configured for this cycle.")
    else:
        result = mechanical_loss_model.evaluate_2t(
            indicated_work_j=work, displacement_m3=displacement,
            rpm=rpm, load=load)
        for name, key in (("brake_work_j", "brake_work_j"),
                          ("brake_power_w", "brake_power_w"),
                          ("brake_torque_nm", "brake_torque_nm"),
                          ("bmep_pa", "brake_mep_pa"),
                          ("fmep_pa", "friction_mep_pa")):
            defined(name, float(result[key]), f"MechanicalLossModel.evaluate_2t: {key}")
        brake_power = float(result["brake_power_w"])
    if brake_power is not None and brake_power > 0.0:
        specific_consumption(brake_power, "bsfc_g_kwh")
    else:
        undefined("bsfc_g_kwh", "Positive brake power requires an explicit loss model.")
    for name in ("gross_work_j", "net_work_j"):
        undefined(name, "Gross/net work separation is not defined by this integrated model.")
    for name in ("delivery_ratio", "trapping_efficiency", "scavenging_efficiency",
                 "charging_efficiency", "trapping_ratio", "residual_fraction",
                 "purity_at_transfer_close", "purity_at_exhaust_close",
                 "short_circuit_fraction", "fresh_retained_kg", "fresh_lost_kg"):
        undefined(name, "Exact geometric port-closure composition snapshots are not yet collected.")
    closures = cycle_record.get("port_closure_snapshots", {})
    if (isinstance(closures, dict) and
            closures.get("status") == "EXACT_EVENT_STATES_CAPTURED"):
        exhaust_snapshot = closures.get("snapshots", {}).get("exhaust")
        if not isinstance(exhaust_snapshot, dict):
            raise ValueError("exact port-closure record lacks exhaust snapshot")
        close_species = exhaust_snapshot.get("cylinder_species_kg")
        if not isinstance(close_species, (list, tuple)) or len(close_species) != 4:
            raise ValueError("exact exhaust-closure species snapshot is invalid")
        close_species = validate_species(close_species, fsum(close_species))
        defined("cylinder_fuel_species_at_exhaust_close_kg", close_species[1],
                "accepted cylinder fuel pseudo-species at exact exhaust closure; "
                "not total trapped fuel")
    if (scavenging_reference_mass_kg is not None and isinstance(closures, dict) and
            closures.get("status") == "EXACT_EVENT_STATES_CAPTURED"):
        from .scavenging import ScavengingInput, calculate_scavenging_metrics
        metrics_record = calculate_scavenging_metrics(ScavengingInput(
            reference_mass_kg=scavenging_reference_mass_kg,
            fresh_delivered_kg=integrals["fresh_delivery_kg"],
            fresh_short_circuit_kg=integrals["fresh_short_circuit_kg"],
            species_at_transfer_close_kg=tuple(
                closures["snapshots"]["transfer"]["cylinder_species_kg"]),
            species_at_exhaust_close_kg=tuple(
                closures["snapshots"]["exhaust"]["cylinder_species_kg"])))
        from .scavenging import scavenging_engineering_records
        metrics.update(scavenging_engineering_records(metrics_record))
    for name in ("ca10_deg", "ca50_deg", "ca90_deg"):
        undefined(name, "Combustion-fraction landmarks are not part of the current P7 source record.")

    return build_integrated_engineering_output_v3(
        rpm=rpm, cycle_number=cycle_number,
        angles_deg=tuple(row[0] - float(start) for row in rows),
        channels=channels, cycle_metrics=metrics,
        dependency_status="CONDITIONAL_ON_P4",
        configuration_sha256=cycle_record["configuration_hash"])
