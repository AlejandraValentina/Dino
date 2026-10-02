from copy import deepcopy
import json

import pytest

from motorsim.gas1d.mesh import uniform_mesh
from motorsim.gas1d.boundary import Boundary
from motorsim.integrated_2t import (
    DuctPath2T, EngineGeometry2T, IntegratedEngine2T,
)
from motorsim.p6_species import SPECIES
from motorsim.reed import ReedPetal
from motorsim.thermal import ThermalSurface, ThermalSystem


def _case(*, crankcase_pressure=130000.0, cylinder_pressure=101325.0,
          exhaust_area=0.0, thermal_system=None, thermal_locations=None,
          geometry=None, max_cfl=0.4, duct_pressure=101325.0,
          reed_petals=(), intake_area=0.0, transfer_pressure=101325.0,
          transfer_area=1e-5, duct_length=.02):
    paths = (
        DuctPath2T("intake", uniform_mesh(2, duct_length, 1e-4), "intake"),
        DuctPath2T("primary", uniform_mesh(2, duct_length, 1e-4), "transfer"),
        DuctPath2T("secondary", uniform_mesh(2, duct_length, 1e-4), "transfer"),
        DuctPath2T("boost", uniform_mesh(2, duct_length, 1e-4), "transfer"),
        DuctPath2T("exhaust", uniform_mesh(2, duct_length, 1e-4), "exhaust"),
    )

    if geometry is None:
        def geometry(angle):
            return EngineGeometry2T(.00015, .00018, 0.0, 0.0, intake_area,
                                    (transfer_area, transfer_area, transfer_area), exhaust_area)

    states = {path.id: ((1.1768, 0.0,
                         transfer_pressure if path.role == "transfer" else duct_pressure,
                         1.0),) * 2 for path in paths}
    component_species = {
        "crankcase": (0.0, 0.0, 0.00017652, 0.0),
        "cylinder": (0.000211824, 0.0, 0.0, 0.0),
    }
    for path in paths:
        if path.role == "transfer":
            component_species[path.id] = tuple(
                (1.1768 * volume, 0.0, 0.0, 0.0) for volume in path.mesh.volumes)
    return IntegratedEngine2T(
        (1.1768, 0.0, crankcase_pressure, 1.0),
        (1.1768, 0.0, cylinder_pressure, 1.0),
        paths, states, geometry, species=component_species,
        inlet_boundary=Boundary("nonreflecting", state=(1.1768, 0.0, 101325.0, 1.0)),
        outlet_boundary=Boundary("nonreflecting", state=(1.1768, 0.0, 101325.0, 1.0)),
        geometry_identity={"fixture": "three-transfer-static-volume-v1"},
        reed_petals=reed_petals,
        thermal_system=thermal_system, thermal_locations=thermal_locations,
        max_cfl=max_cfl)


def test_integrated_topology_resolves_three_transfer_routes_and_ledgers():
    system = _case()
    before = system.inventory()
    record = system.step(1e-8, .01)
    report = system.conservation_report()

    assert set(record["stage_face_fluxes"][0]) == {
        "intake", "primary", "secondary", "boost", "exhaust"}
    assert len(record["stage_geometry"]) == 2
    assert all(abs(report["species"][name]["residual"]) < 1e-15 for name in SPECIES)
    assert abs(report["mass"]["residual"]) < 1e-15
    assert abs(report["energy"]["residual"]) < 1e-10
    # Pressure drives the crankcase donor through the generic transfer routes.
    assert system.state["species"]["chambers"]["crankcase"][2] < before["species_kg"][2]
    assert all(sum(values) == pytest.approx(
        system.state["ducts"][path_id][i][0] * path.mesh.volumes[i], abs=1e-14)
        for path in system.transfers for path_id in (path.id,)
        for i, values in enumerate(system.state["species"]["ducts"][path_id]))


def test_integrated_engine_checkpoint_restart_replays_identically():
    continuous = _case()
    continuous.step(1e-8, .01)
    checkpoint = continuous.snapshot()
    split = _case()
    split.restore(deepcopy(checkpoint))

    continuous.step(1e-8, .01)
    split.step(1e-8, .01)
    assert continuous.inventory() == split.inventory()
    assert continuous.conservation_report() == split.conservation_report()
    assert continuous.state == split.state
    json_checkpoint = json.loads(json.dumps(continuous.snapshot()))
    restored = _case()
    restored.restore(json_checkpoint)
    assert json.dumps(restored.state, sort_keys=True) == json.dumps(
        continuous.state, sort_keys=True)
    assert restored.conservation_report() == continuous.conservation_report()


def test_integrated_engine_rejects_incomplete_or_non_generic_topology():
    system = _case()
    with pytest.raises(ValueError, match="at least three transfers"):
        IntegratedEngine2T(
            (1.1768, 0.0, 101325.0, 1.0), (1.1768, 0.0, 101325.0, 1.0),
            system.ducts[:4], {path.id: ((1.1768, 0.0, 101325.0, 1.0),) * 2
                               for path in system.ducts[:4]},
            system.geometry, geometry_identity={"fixture": "invalid-topology"})


def test_integrated_engine_enforces_cfl_without_accepting_partial_state():
    system = _case()
    original = deepcopy(system.snapshot())
    with pytest.raises(ValueError, match="CFL limit exceeded"):
        system.step(1e-4, .01)
    assert system.state == original["state"]
    assert system.accepted_steps == 0
    assert system.rejected_steps == 1


def test_integrated_cfl_also_bounds_zero_dimensional_chamber_depletion():
    system = _case(crankcase_pressure=1e7, max_cfl=0.1)
    original = deepcopy(system.snapshot())
    with pytest.raises(ValueError, match="CFL limit exceeded"):
        system.step(6e-7, .01)
    assert system.state == original["state"]
    assert system.accepted_steps == 0


def test_integrated_chamber_cfl_uses_gross_turnover_not_net_mass_rate():
    petal = ReedPetal("intake-petal", .001, 1e-4, .01, 10.0, .01,
                      .002, .8, "SYNTHETIC_ASSUMPTION")
    system = _case(crankcase_pressure=130000.0, duct_pressure=150000.0,
                   intake_area=1e-5, transfer_pressure=101325.0,
                   reed_petals=(petal,), transfer_area=1e-6,
                   duct_length=3000.0, max_cfl=0.6)
    assembled = system._assemble(system.state, 0.0, 1000.0)
    net_rate = assembled["q"]["chambers"]["crankcase"][0]
    gross_outflow = assembled["chamber_outflow_kg_s"]["crankcase"]
    assert net_rate > 0.0  # inlet dominates, but transfer outflow is simultaneous
    assert gross_outflow > 0.0
    dt = system.state["chambers"]["crankcase"][0] / gross_outflow * 0.5
    cfl = system._cfl(system.state, assembled, dt)
    assert cfl >= 0.5
    assert dt * max(0.0, -net_rate) / system.state["chambers"]["crankcase"][0] == 0.0


@pytest.mark.parametrize("field, message", [
    ("angle", "wrapped/unwrapped angle mismatch"),
    ("volume", "cylinder geometry mismatch"),
])
def test_integrated_checkpoint_rejects_inconsistent_clock_or_geometry_atomically(
        field, message):
    source = _case()
    source.step(1e-8, .01)
    snapshot = deepcopy(source.snapshot())
    if field == "angle":
        snapshot["angle_deg"] = 1.0
    else:
        chamber = snapshot["state"]["chambers"]["cylinder"]
        snapshot["state"]["chambers"]["cylinder"] = (*chamber[:2], .00019)
    target = _case()
    before = deepcopy(target.snapshot())
    with pytest.raises(ValueError, match=message):
        target.restore(snapshot)
    assert target.snapshot() == before


def test_integrated_checkpoint_rejects_geometry_callback_mismatch():
    source = _case()
    source.step(1e-8, .01)

    def different_geometry(angle):
        return EngineGeometry2T(.00015, .00018 if angle == 0 else .00019, 0.0, 0.0, 0.0,
                                (1e-5, 1e-5, 1e-5), 0.0)

    target = _case(geometry=different_geometry)
    with pytest.raises(ValueError, match="cylinder geometry mismatch"):
        target.restore(source.snapshot())


def test_integrated_backflow_uses_the_actual_duct_species_donor():
    system = _case(crankcase_pressure=90000.0)
    initial_fresh = system.state["species"]["chambers"]["crankcase"][0]
    system.step(1e-8, .01)
    final = system.state["species"]["chambers"]["crankcase"]
    assert final[0] > initial_fresh
    assert final[2] == pytest.approx(.00017652, abs=1e-15)


def test_static_reed_is_evaluated_from_each_shared_stage_pressure():
    petal = ReedPetal("intake-petal", .001, 1e-4, .01, 10.0, .01,
                      .002, .8, "SYNTHETIC_ASSUMPTION")
    closed = _case(reed_petals=(petal,), intake_area=1e-5)
    closed_record = closed.step(1e-8, .01)
    assert closed_record["stage_face_fluxes"][0]["intake"][
        "effective_reed_area_m2"] == 0.0

    open_system = _case(reed_petals=(petal,), duct_pressure=150000.0,
                        intake_area=1e-5)
    open_record = open_system.step(1e-8, .01)
    assert open_record["stage_face_fluxes"][0]["intake"][
        "effective_reed_area_m2"] > 0.0
    assert open_record["stage_face_fluxes"][0]["intake"][
        "right_species"][0] > 0.0


def test_fresh_exhaust_flow_is_counted_as_short_circuit_only_with_open_transfers():
    system = _case(cylinder_pressure=130000.0, exhaust_area=1e-5)
    system.step(1e-8, .01)
    assert system.ledger["fresh_short_circuit_kg"] > 0.0


def test_prescribed_wall_heat_uses_stage_state_and_global_energy_ledger():
    thermal = ThermalSystem((ThermalSurface(
        "cylinder-wall", "cylinder_wall", 1e-4, 1000.0,
        "SYNTHETIC_ASSUMPTION", wall_temperature_K=290.0),))
    system = _case(thermal_system=thermal,
                   thermal_locations={"cylinder-wall": "cylinder"})
    record = system.step(1e-8, .01)
    assert record["heat_to_wall_J"] > 0.0
    assert system.ledger["heat_to_wall_J"] == record["heat_to_wall_J"]
    assert abs(system.conservation_report()["energy"]["residual"]) < 1e-10
