"""Generic, stage-coherent 2T finite-volume engine integration.

This is an orchestration layer over the existing Euler EOS, mesh, HLLC and
0D/1D Riemann interface.  It does not alter the historical P5/P6 campaign
implementations or add another numerical flux law.  Four species are stored
as extensive masses and are authoritative; the legacy passive scalar in the
Euler vector is regenerated as total mass density.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from math import fsum, isfinite
from typing import Callable

from .coupling import ChamberState, interface_flux
from .gas1d.boundary import Boundary
from .gas1d.eos import IdealGas
from .gas1d.riemann import hllc_flux
from .p6_species import (SPECIES, atmospheric_species, donor_species,
                         legacy_to_species, validate_species)
from .reed import ReedPetal, static_area
from .thermal import ThermalSystem


def _tuplify(value):
    if isinstance(value, list):
        return tuple(_tuplify(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuplify(item) for key, item in value.items()}
    return value


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
class DuctPath2T:
    id: str
    mesh: object
    role: str

    def validate(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("duct path requires a stable id")
        if self.role not in {"intake", "transfer", "exhaust"}:
            raise ValueError("unsupported duct role")
        if not getattr(self.mesh, "volumes", None) or not getattr(self.mesh, "areas", None):
            raise ValueError("duct path requires an existing finite-volume mesh")
        if len(self.mesh.areas) != len(self.mesh.volumes) + 1:
            raise ValueError("duct mesh face/cell shape mismatch")


class IntegratedEngine2T:
    """One SSPRK2 state for reed/intake-ready, N-transfer, exhaust topology.

    ``geometry(angle_deg)`` must return an :class:`EngineGeometry2T` with exact
    stage volumes and effective areas.  Boundary conditions are explicit
    existing ``Boundary`` objects.  The default atmosphere uses the existing
    P6 composition (fresh air only).  Source/reed state can be added to this
    same state by subsequent adapters; no out-of-band stage mutation is used.
    """
    schema = "MOTORSIM_INTEGRATED_ENGINE_2T_STATE_V1"
    dependency_status = "CONDITIONAL_ON_P4"

    def __init__(self, crankcase_state: tuple, cylinder_state: tuple,
                 ducts: tuple[DuctPath2T, ...], initial_duct_states: dict[str, tuple],
                 geometry: Callable[[float], EngineGeometry2T], *,
                 eos: IdealGas | None = None,
                 species: dict | None = None,
                 atmosphere: tuple = (101325.0, 300.0),
                 atmosphere_species: tuple | None = None,
                 inlet_boundary: Boundary | None = None,
                 outlet_boundary: Boundary | None = None,
                 max_cfl: float = 0.4,
                 geometry_identity: dict | None = None,
                 reed_petals: tuple[ReedPetal, ...] = (),
                 thermal_system: ThermalSystem | None = None,
                 thermal_locations: dict[str, str] | None = None,
                 thermal_load: float = 0.0):
        self.eos = eos or IdealGas()
        self.geometry = geometry
        if not isinstance(geometry_identity, dict) or not geometry_identity:
            raise ValueError("stable geometry_identity is required for restart/replay")
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
        if type(max_cfl) not in (int, float) or not isfinite(max_cfl) or not 0 < max_cfl <= 1:
            raise ValueError("max_cfl must be finite and in (0, 1]")
        self.max_cfl = float(max_cfl)
        if not callable(geometry):
            raise ValueError("stage geometry callback is required")
        if (not isinstance(ducts, tuple) or len(ducts) < 3 or
                sum(path.role == "intake" for path in ducts) != 1 or
                sum(path.role == "exhaust" for path in ducts) != 1 or
                sum(path.role == "transfer" for path in ducts) < 3):
            raise ValueError("topology requires intake, exhaust and at least three transfers")
        for path in ducts:
            path.validate()
        if len({path.id for path in ducts}) != len(ducts):
            raise ValueError("duct ids must be unique")
        self.ducts = ducts
        self.intake = next(path for path in ducts if path.role == "intake")
        self.exhaust = next(path for path in ducts if path.role == "exhaust")
        self.transfers = tuple(path for path in ducts if path.role == "transfer")
        if set(initial_duct_states) != {path.id for path in ducts}:
            raise ValueError("initial duct states must match topology ids exactly")
        p_atm, t_atm = atmosphere
        if (not all(type(x) in (int, float) and isfinite(x) and x > 0
                    for x in (p_atm, t_atm))):
            raise ValueError("atmosphere pressure and temperature must be positive")
        self.atmosphere_state = self.eos.validate((p_atm / (self.eos.R * t_atm), 0.0,
                                                   p_atm, 1.0))
        self.atmosphere_species = tuple(atmosphere_species or atmospheric_species())
        validate_species(self.atmosphere_species, 1.0)
        self.inlet_boundary = inlet_boundary or Boundary(
            "reservoir", p0=p_atm, T0=t_atm, Y0=1.0)
        self.outlet_boundary = outlet_boundary or Boundary(
            "reservoir", p0=p_atm, T0=t_atm, Y0=1.0)
        self.thermal_system = thermal_system
        self.thermal_load = float(thermal_load)
        if not isfinite(self.thermal_load) or self.thermal_load < 0:
            raise ValueError("thermal load must be finite and nonnegative")
        self.thermal_locations = dict(thermal_locations or {})
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
                       "heat_to_wall_J": 0.0,
                       "cylinder_work_J": 0.0, "crankcase_work_J": 0.0}
        self.trace = []
        geometry0 = self._geometry(self.angle_deg)
        self.state = {
            "chambers": {
                "crankcase": self._chamber_from_primitive(crankcase_state,
                                                           geometry0.crankcase_volume_m3),
                "cylinder": self._chamber_from_primitive(cylinder_state,
                                                         geometry0.cylinder_volume_m3)},
            "ducts": {}, "species": {"chambers": {}, "ducts": {}},
        }
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

    def _chamber_from_primitive(self, primitive, volume):
        rho, velocity, pressure, _ = primitive
        if velocity != 0:
            raise ValueError("0D chamber macroscopic velocity must be zero")
        return (rho * volume, pressure * volume / (self.eos.gamma - 1.0), volume)

    def _configuration_identity(self):
        initial_payload = {"state": self.state,
                           "atmosphere": self.atmosphere_state,
                           "atmosphere_species": self.atmosphere_species}
        initial_bytes = json.dumps(initial_payload, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode("utf-8")
        identity = {"ducts": [{"id": path.id, "role": path.role,
                               "mesh": path.mesh.as_dict()} for path in self.ducts],
                    "transfer_ids": [path.id for path in self.transfers],
                    "eos": {"R": self.eos.R, "gamma": self.eos.gamma},
                    "species": list(SPECIES), "state_schema": self.schema,
                    "max_cfl": self.max_cfl, "geometry_sha256": self.geometry_sha256,
                    "reed": [petal.to_dict() for petal in self.reed_petals],
                    "initial_state_sha256": hashlib.sha256(initial_bytes).hexdigest(),
                    "boundaries": {"inlet": vars(self.inlet_boundary),
                                   "outlet": vars(self.outlet_boundary)},
                    "thermal": (None if self.thermal_system is None else
                                self.thermal_system.to_dict()),
                    "thermal_locations": self.thermal_locations,
                    "thermal_load": self.thermal_load}
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                             allow_nan=False)
        normalized = json.loads(encoded)
        normalized["configuration_sha256"] = hashlib.sha256(
            encoded.encode("utf-8")).hexdigest()
        return normalized

    def _geometry(self, angle):
        result = self.geometry(float(angle) % 360.0)
        if not isinstance(result, EngineGeometry2T):
            raise ValueError("geometry callback must return EngineGeometry2T")
        result.validate(tuple(path.id for path in self.transfers) if hasattr(self, "transfers")
                        else tuple(path.id for path in self.ducts if path.role == "transfer"))
        return result

    def _chamber_state(self, chamber, species):
        mass, energy, volume = chamber
        if mass <= 0 or energy <= 0 or volume <= 0:
            raise ValueError("inadmissible 0D chamber state")
        pressure = (self.eos.gamma - 1.0) * energy / volume
        fresh_fraction = fsum(species[:2]) / mass
        return ChamberState(mass, energy, mass * fresh_fraction, volume)

    def _primitive(self, q):
        return self.eos.primitive((q[0], q[1], q[2], q[0]))

    @staticmethod
    def _fractions(species, mass):
        validate_species(species, mass)
        return tuple(value / mass for value in species)

    def _face_species_flux(self, mass_flux, left_species, left_mass,
                           right_species, right_mass):
        donor_left = self._fractions(left_species, left_mass)
        donor_right = self._fractions(right_species, right_mass)
        return donor_species(mass_flux, donor_left, donor_right)

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
            right_comp = self.atmosphere_species
            right_mass = 1.0
        species_flux = self._face_species_flux(face[0], left_comp, left_mass,
                                               right_comp, right_mass)
        return face, species_flux, max(abs(speeds[0]), abs(speeds[-1]))

    def _assemble(self, state, angle, rpm):
        """Build every RHS from one immutable stage state."""
        g = self._geometry(angle)
        chambers = state["chambers"]
        species_chambers = state["species"]["chambers"]
        cc = self._chamber_state(chambers["crankcase"], species_chambers["crankcase"])
        cy = self._chamber_state(chambers["cylinder"], species_chambers["cylinder"])
        rhs_q = {"chambers": {"crankcase": [0.0, 0.0, 0.0],
                               "cylinder": [0.0, 0.0, 0.0]}, "ducts": {}}
        chamber_outflow = {"crankcase": 0.0, "cylinder": 0.0}
        rhs_s = {"chambers": {"crankcase": [0.0] * 4,
                               "cylinder": [0.0] * 4}, "ducts": {}}
        faces_trace = {}
        external = {"mass": 0.0, "energy": 0.0, "species": [0.0] * 4}
        fresh_delivered_rate = 0.0
        fresh_short_circuit_rate = 0.0
        fuel_delivered_rate = 0.0
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
                external_l, species_l, speed_l = self._external_face(
                    state, path, "left", self.inlet_boundary)
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
                right_face = ((0.0, 0.0, 0.0) if right_exchange is None else
                              right_exchange.flux_x[:3])
                speed_r = (max(abs(primitives[-1][1] - self.eos.sound_speed(primitives[-1])),
                               abs(primitives[-1][1] + self.eos.sound_speed(primitives[-1])))
                           if right_exchange is None else
                           max(abs(right_exchange.wave_speeds[0]),
                               abs(right_exchange.wave_speeds[-1])))
                right_species = ((0.0,) * 4 if right_exchange is None else
                    self._face_species_flux(right_face[0], ss[-1], qs[-1][0]*path.mesh.volumes[-1],
                                            species_chambers["crankcase"], chambers["crankcase"][0]))
                # A left face points in +x; it is an external inflow when positive.
                external["mass"] += external_l[0]
                external["energy"] += external_l[2]
                for j, value in enumerate(species_l): external["species"][j] += value
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
                left_face = (0.0, 0.0, 0.0) if left_exchange is None else left_exchange.flux_x[:3]
                right_face = (0.0, 0.0, 0.0) if right_exchange is None else right_exchange.flux_x[:3]
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
                external_r, species_r, speed_r = self._external_face(
                    state, path, "right", self.outlet_boundary)
                left_face = (0.0, 0.0, 0.0) if left_exchange is None else left_exchange.flux_x[:3]
                speed_l = (max(abs(primitives[0][1] - self.eos.sound_speed(primitives[0])),
                               abs(primitives[0][1] + self.eos.sound_speed(primitives[0])))
                           if left_exchange is None else
                           max(abs(left_exchange.wave_speeds[0]), abs(left_exchange.wave_speeds[-1])))
                left_species = ((0.0,) * 4 if left_exchange is None else
                    self._face_species_flux(left_face[0], species_chambers["cylinder"],
                                            chambers["cylinder"][0], ss[0],
                                            qs[0][0]*path.mesh.volumes[0]))
                if (left_exchange is not None and g.exhaust_area_m2 > 0 and
                        any(area > 0 for area in g.transfer_areas_m2)):
                    fresh_short_circuit_rate += max(0.0, left_species[0] + left_species[1])
                if left_exchange is not None:
                    chamber_outflow["cylinder"] += max(0.0, -left_exchange.outward[0])
                    rhs_q["chambers"]["cylinder"][0] += left_exchange.outward[0]
                    rhs_q["chambers"]["cylinder"][1] += left_exchange.outward[2]
                    for j, value in enumerate(left_species): rhs_s["chambers"]["cylinder"][j] -= value
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
                donor = ss[i] if mflux >= 0 else ss[i + 1]
                donor_mass = qs[i if mflux >= 0 else i + 1][0] * path.mesh.volumes[i if mflux >= 0 else i + 1]
                receiver = ss[i + 1] if mflux >= 0 else ss[i]
                receiver_mass = qs[i + 1 if mflux >= 0 else i][0] * path.mesh.volumes[i + 1 if mflux >= 0 else i]
                sf = self._face_species_flux(mflux, donor, donor_mass, receiver, receiver_mass)
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
                "external": external, "work_rates": work,
                "fresh_delivered_rate": fresh_delivered_rate,
                "fresh_short_circuit_rate": fresh_short_circuit_rate,
                "fuel_delivered_rate": fuel_delivered_rate,
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
            self.eos.validate((mass/volume, 0.0, pressure, fsum(comp[:2])/mass))
        for path in self.ducts:
            for i, q in enumerate(state["ducts"][path.id]):
                volume = path.mesh.volumes[i]
                self.eos.primitive((q[0], q[1], q[2], q[0]))
                validate_species(state["species"]["ducts"][path.id][i], q[0]*volume)

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
        return {"mass_kg": mass, "energy_J": energy, "species_kg": tuple(species)}

    def step(self, dt_s: float, delta_angle_deg: float):
        if (type(dt_s) not in (int, float) or not isfinite(dt_s) or dt_s <= 0 or
                type(delta_angle_deg) not in (int, float) or not isfinite(delta_angle_deg)
                or delta_angle_deg <= 0):
            raise ValueError("time and crank-angle increments must be positive finite values")
        start_angle = self.crank_angle_unwrapped_deg
        end_angle = start_angle + float(delta_angle_deg)
        q0 = deepcopy(self.state)
        self._validate(q0)
        rpm = float(delta_angle_deg) / (6.0 * float(dt_s))
        r0 = self._assemble(q0, start_angle, rpm)
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
        g1 = self._geometry(end_angle)
        q1["chambers"]["crankcase"] = (*q1["chambers"]["crankcase"][:2], g1.crankcase_volume_m3)
        q1["chambers"]["cylinder"] = (*q1["chambers"]["cylinder"][:2], g1.cylinder_volume_m3)
        for path in self.ducts:
            for i, q in enumerate(q1["ducts"][path.id]):
                rho = fsum(q1["species"]["ducts"][path.id][i])/path.mesh.volumes[i]
                q1["ducts"][path.id][i] = (q[0], q[1], q[2], rho)
        self._validate(q1)
        r1 = self._assemble(q1, end_angle, rpm)
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
        wall_rates_0, wall_rates_1 = r0["thermal_rates"], r1["thermal_rates"]
        if set(wall_rates_0) != set(wall_rates_1):
            raise ValueError("thermal surface set changed between SSPRK2 stages")
        heat_to_wall = .5*dt_s*fsum(wall_rates_0.values()) + .5*dt_s*fsum(wall_rates_1.values())
        self.ledger["heat_to_wall_J"] += heat_to_wall
        self.ledger["crankcase_work_J"] += .5*dt_s*(r0["work_rates"]["crankcase"]+
                                                     r1["work_rates"]["crankcase"])
        self.ledger["cylinder_work_J"] += .5*dt_s*(r0["work_rates"]["cylinder"]+
                                                   r1["work_rates"]["cylinder"])
        trace = {"angle_start_deg": start_angle, "angle_end_deg": end_angle,
                 "time_start_s": self.time_s, "dt_s": float(dt_s),
                 "rpm": float(delta_angle_deg) / (6.0 * float(dt_s)),
                 "stage_states": (q0, q1, qn),
                 "stage_face_fluxes": (r0["faces"], r1["faces"]),
                 "stage_external": (r0["external"], r1["external"]),
                 "stage_geometry": (vars(r0["geometry"]), vars(r1["geometry"])),
                 "stage_work_rates": (r0["work_rates"], r1["work_rates"]),
                 "stage_thermal_rates": (wall_rates_0, wall_rates_1),
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
                                       self.ledger["crankcase_work_J"]-
                                       self.ledger["cylinder_work_J"]+
                                       self.ledger["heat_to_wall_J"]},
                "species": {SPECIES[i]: {"initial": self.initial_inventory["species_kg"][i],
                                         "final": final["species_kg"][i],
                                         "external": self.ledger["external_species_kg"][i],
                                         "residual": delta_species[i]-
                                                    self.ledger["external_species_kg"][i]}
                            for i in range(4)}}

    def snapshot(self):
        return {"schema": self.schema, "configuration_identity": deepcopy(self.configuration_identity),
                "state": deepcopy(self.state), "angle_deg": self.angle_deg,
                "crank_angle_unwrapped_deg": self.crank_angle_unwrapped_deg,
                "time_s": self.time_s, "cycle": self.cycle,
                "accepted_steps": self.accepted_steps,
                "rejected_steps": self.rejected_steps,
                "max_cfl": self.max_cfl,
                "ledger": deepcopy(self.ledger),
                "initial_inventory": deepcopy(self.initial_inventory),
                "trace": deepcopy(self.trace)}

    def restore(self, snapshot):
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
                         "heat_to_wall_J", "cylinder_work_J", "crankcase_work_J"}
        if not isinstance(ledger, dict) or set(ledger) != ledger_fields:
            raise ValueError("integrated engine checkpoint ledger schema mismatch")
        if (not isinstance(ledger["external_species_kg"], (list, tuple)) or
                len(ledger["external_species_kg"]) != 4 or
                any(type(value) not in (int, float) or not isfinite(value)
                    for key, value in ledger.items()
                    for value in (ledger[key] if key == "external_species_kg" else (value,)))):
            raise ValueError("integrated engine checkpoint ledger contains invalid values")
        baseline = json.loads(json.dumps(self.initial_inventory, sort_keys=True))
        initial = json.loads(json.dumps(snapshot.get("initial_inventory"), sort_keys=True))
        if initial != baseline:
            raise ValueError("integrated engine checkpoint initial inventory mismatch")
        trace = snapshot.get("trace")
        if not isinstance(trace, list) or len(trace) != counters[1]:
            raise ValueError("integrated engine checkpoint primary trace is incomplete")
        # Commit restored values only after the entire checkpoint passes validation.
        self.state = state
        self.angle_deg = float(angle)
        self.crank_angle_unwrapped_deg = float(unwrapped)
        self.time_s = float(time_s)
        self.cycle, self.accepted_steps, self.rejected_steps = counters
        self.ledger = ledger
        self.initial_inventory = deepcopy(snapshot["initial_inventory"])
        self.trace = deepcopy(trace)
