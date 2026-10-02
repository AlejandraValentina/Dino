from copy import deepcopy
import json

import pytest

from motorsim.gas1d.mesh import uniform_mesh
from motorsim.gas1d.boundary import Boundary
from motorsim.crankcase import CrankcaseGeometry
from motorsim.expansion_chamber import ChamberSection, ExpansionChamber
from motorsim.integrated_2t import (
    DuctPath2T, EngineGeometry2T, IntegratedEngine2T, IntegratedPortBinding2T,
    SliderCrankChambers2T,
)
from motorsim.kinematics import piston_position
from motorsim.p6_species import SPECIES
from motorsim.powervalve import PowerValve
from motorsim.reed import ReedPetal
from motorsim.thermal import ThermalSurface, ThermalSystem
from motorsim.two_stroke_ports import AreaKnot, DuctBinding, PortDefinition, TwoStrokePortSet


def _case(*, crankcase_pressure=130000.0, cylinder_pressure=101325.0,
          exhaust_area=0.0, thermal_system=None, thermal_locations=None,
          geometry=None, max_cfl=0.4, duct_pressure=101325.0,
          reed_petals=(), intake_area=0.0, transfer_pressure=101325.0,
          transfer_area=1e-5, duct_length=.02, exhaust_mesh=None,
          port_binding=None, reference_rpm=1000.0, geometry_identity=None,
          duct_species=None, slider_crank=None,
          combustion_start_angle_deg=None, cylinder_species=None):
    def duct_mesh(duct_id):
        if duct_id == "exhaust" and exhaust_mesh is not None:
            return exhaust_mesh
        return uniform_mesh(2, duct_length, 1e-4)

    paths = (
        DuctPath2T("intake", duct_mesh("intake"), "intake"),
        DuctPath2T("primary", duct_mesh("primary"), "transfer"),
        DuctPath2T("secondary", duct_mesh("secondary"), "transfer"),
        DuctPath2T("boost", duct_mesh("boost"), "transfer"),
        DuctPath2T("exhaust", duct_mesh("exhaust"), "exhaust"),
    )

    if geometry is None:
        def geometry(angle):
            return EngineGeometry2T(.00015, .00018, 0.0, 0.0, intake_area,
                                    (transfer_area, transfer_area, transfer_area), exhaust_area)

    states = {path.id: ((1.1768, 0.0,
                         transfer_pressure if path.role == "transfer" else duct_pressure,
                         1.0),) * len(path.mesh.volumes) for path in paths}
    component_species = {
        "crankcase": (0.0, 0.0, 0.00017652, 0.0),
        "cylinder": (0.000211824, 0.0, 0.0, 0.0),
    }
    if cylinder_species is not None:
        component_species["cylinder"] = tuple(cylinder_species)
    if slider_crank is not None:
        crankcase_volume, cylinder_volume, _, _ = slider_crank.resolve(
            0.0, reference_rpm)
        component_species["crankcase"] = (
            0.0, 0.0, 1.1768 * crankcase_volume, 0.0)
        component_species["cylinder"] = (
            1.1768 * cylinder_volume, 0.0, 0.0, 0.0)
    for path in paths:
        if path.role == "transfer":
            component_species[path.id] = tuple(
                (1.1768 * volume, 0.0, 0.0, 0.0) for volume in path.mesh.volumes)
    component_species.update(duct_species or {})
    return IntegratedEngine2T(
        (1.1768, 0.0, crankcase_pressure, 1.0),
        (1.1768, 0.0, cylinder_pressure, 1.0),
        paths, states, geometry, species=component_species,
        inlet_boundary=Boundary("nonreflecting", state=(1.1768, 0.0, 101325.0, 1.0)),
        outlet_boundary=Boundary("nonreflecting", state=(1.1768, 0.0, 101325.0, 1.0)),
        geometry_identity=(geometry_identity or
                           {"fixture": "three-transfer-static-volume-v1"}),
        reed_petals=reed_petals,
        port_binding=port_binding, slider_crank=slider_crank,
        reference_rpm=reference_rpm,
        thermal_system=thermal_system, thermal_locations=thermal_locations,
        combustion_start_angle_deg=combustion_start_angle_deg,
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


def test_existing_crankcase_v2_drives_both_chamber_volumes_in_integrated_stages():
    crankcase = CrankcaseGeometry(56.0, 50.0, 100.0, 20.0,
                                  "SYNTHETIC_ASSUMPTION")
    model = SliderCrankChambers2T(crankcase, 8.0)
    geometry = model.resolve(90.0, 3000.0)
    assert geometry[0] == pytest.approx(crankcase.volume_m3(90.0))
    assert geometry[1] == pytest.approx(
        crankcase.displacement_m3 / 7.0 +
        crankcase.displacement_m3 * piston_position(50.0, 100.0, 90.0) / 50.0)
    assert geometry[2] == pytest.approx(crankcase.volume_rate_m3_s(90.0, 3000.0))
    assert geometry[3] == pytest.approx(-geometry[2])

    system = _case(crankcase_pressure=101325.0, cylinder_pressure=101325.0,
                   slider_crank=model, reference_rpm=3000.0,
                   geometry_identity={"slider_crank": model.to_dict(),
                                      "fixture": "shared-2t-slider-crank-v1"})
    initial = system._geometry(0.0, 3000.0)
    initial_volumes = (system.state["chambers"]["crankcase"][2],
                       system.state["chambers"]["cylinder"][2])
    assert initial_volumes == pytest.approx((initial.crankcase_volume_m3,
                                             initial.cylinder_volume_m3))
    record = system.step(1.25e-6, 0.0225)
    expected_end = model.resolve(0.0225, 3000.0)
    assert system.state["chambers"]["crankcase"][2] == pytest.approx(expected_end[0])
    assert system.state["chambers"]["cylinder"][2] == pytest.approx(expected_end[1])
    assert record["stage_geometry"][0]["crankcase_volume_rate_m3_s"] == pytest.approx(
        model.resolve(0.0, 3000.0)[2], rel=1e-6, abs=1e-15)
    assert record["stage_geometry"][1]["crankcase_volume_rate_m3_s"] == pytest.approx(
        expected_end[2], rel=1e-6, abs=1e-15)
    assert abs(system.conservation_report()["mass"]["residual"]) < 1e-14
    assert abs(system.conservation_report()["energy"]["residual"]) < 1e-10

    mismatched = _case(crankcase_pressure=101325.0, cylinder_pressure=101325.0,
                       slider_crank=SliderCrankChambers2T(crankcase, 9.0),
                       reference_rpm=3000.0,
                       geometry_identity={"slider_crank": model.to_dict(),
                                          "fixture": "shared-2t-slider-crank-v1"})
    with pytest.raises(ValueError, match="configuration mismatch"):
        mismatched.restore(system.snapshot())


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


def test_existing_expansion_chamber_mesh_participates_in_integrated_exhaust_stages():
    chamber = ExpansionChamber((
        ChamberSection("header", "header", 80.0, 20.0, 20.0),
        ChamberSection("diffuser", "diffuser", 180.0, 20.0, 52.0),
        ChamberSection("belly", "belly", 100.0, 52.0, 52.0),
        ChamberSection("baffle", "baffle_cone", 170.0, 52.0, 16.0),
        ChamberSection("stinger", "stinger", 120.0, 16.0, 16.0),
    ))
    exhaust_mesh = chamber.mesh(.01)
    system = _case(cylinder_pressure=130000.0, exhaust_area=1e-5,
                   exhaust_mesh=exhaust_mesh)
    record = system.step(1e-8, .01)
    assert system.exhaust.mesh.as_dict() == exhaust_mesh.as_dict()
    assert len(record["stage_face_fluxes"][0]["exhaust"]["all_faces"]) == len(
        exhaust_mesh.volumes) + 1
    assert len(record["stage_face_fluxes"][1]["exhaust"]["all_species_faces"]) == len(
        exhaust_mesh.volumes) + 1
    assert abs(system.conservation_report()["mass"]["residual"]) < 1e-15
    assert abs(system.conservation_report()["energy"]["residual"]) < 1e-10


def test_generic_ports_and_powervalve_resolve_into_integrated_stage_geometry():
    ports = TwoStrokePortSet(
        56.0, 100.0,
        (DuctBinding("inlet", "intake"),
         DuctBinding("primary", "transfer"),
         DuctBinding("secondary", "transfer"),
         DuctBinding("boost", "transfer"),
         DuctBinding("exhaust", "exhaust")),
        (PortDefinition("inlet-window", "Inlet", "intake", "piston_port", "inlet",
                        "piston_port", .9, "SYNTHETIC_ASSUMPTION", top_mm=64.0,
                        height_mm=10.0, width_mm=20.0, skirt_mm=42.0),
         PortDefinition("primary-window", "Primary", "transfer", "primary", "primary",
                        "rectangular_window", .8, "SYNTHETIC_ASSUMPTION", top_mm=32.0,
                        height_mm=10.0, width_mm=20.0),
         PortDefinition("secondary-window", "Secondary", "transfer", "secondary", "secondary",
                        "rectangular_window", .8, "SYNTHETIC_ASSUMPTION", top_mm=34.0,
                        height_mm=8.0, width_mm=12.0),
         PortDefinition("boost-window", "Boost", "transfer", "boost", "boost",
                        "rectangular_window", .7, "SYNTHETIC_ASSUMPTION", top_mm=36.0,
                        height_mm=7.0, width_mm=8.0),
         PortDefinition("main-exhaust", "Main exhaust", "exhaust", "main", "exhaust",
                        "rectangular_window", .9, "SYNTHETIC_ASSUMPTION", top_mm=30.0,
                        height_mm=10.0, width_mm=20.0, roof_travel_mm=4.0),
         PortDefinition("aux-exhaust", "Aux exhaust", "exhaust", "auxiliary", "exhaust",
                        "effective_profile", .5, "SYNTHETIC_ASSUMPTION",
                        area_profile=(AreaKnot(0.0, 0.0), AreaKnot(90.0, 25.0),
                                      AreaKnot(180.0, 50.0), AreaKnot(270.0, 25.0),
                                      AreaKnot(360.0, 0.0)))))
    valve = PowerValve("pv", "main-exhaust", (1000.0, 5000.0), (0.0, 1.0),
                       "SYNTHETIC_ASSUMPTION")
    path_mapping = {"inlet": "intake", "primary": "primary", "secondary": "secondary",
                    "boost": "boost", "exhaust": "exhaust"}
    binding = IntegratedPortBinding2T(ports, path_mapping, valve)
    path_mapping["primary"] = "secondary"  # caller mutations cannot stale a live binding
    assert binding.path_by_duct["primary"] == "primary"
    with pytest.raises(TypeError):
        binding.path_by_duct["primary"] = "secondary"
    identity = {"ports": ports.to_dict(), "powervalve": valve.to_dict()}
    duct_species = {
        path_id: ((0.0, 0.0, 1.1768e-6, 0.0), (1.1768e-6, 0.0, 0.0, 0.0))
        for path_id in path_mapping.values()
    }
    system = _case(port_binding=binding, reference_rpm=3000.0,
                   cylinder_pressure=130000.0,
                   geometry=lambda angle: EngineGeometry2T(.00015, .00018, 0.0, 0.0,
                                                           0.0, (0.0, 0.0, 0.0), 0.0),
                   geometry_identity=identity, duct_species=duct_species)
    closed = system._geometry(0.0, 3000.0)
    open_stage = system._assemble(system.state, 180.0, 3000.0)
    resolved = open_stage["geometry"]
    assert closed.exhaust_area_m2 < resolved.exhaust_area_m2
    assert len(resolved.transfer_areas_m2) == 3
    assert all(area > 0.0 for area in resolved.transfer_areas_m2)
    assert open_stage["faces"]["exhaust"]["left"][0] != 0.0
    checkpoint = system.snapshot()
    mismatched = _case(port_binding=binding, reference_rpm=3001.0,
                       cylinder_pressure=130000.0,
                       geometry=lambda angle: EngineGeometry2T(
                           .00015, .00018, 0.0, 0.0, 0.0, (0.0, 0.0, 0.0), 0.0),
                       geometry_identity=identity)
    with pytest.raises(ValueError, match="configuration mismatch"):
        mismatched.restore(checkpoint)
    for step_index in range(4000):
        system.step(1.25e-6, 0.0225)
    assert system.angle_deg == pytest.approx(90.0)
    assert any(stage["exhaust_area_m2"] > 0.0
               for trace in system.trace for stage in trace["stage_geometry"])
    assert all(len(trace["stage_face_fluxes"]) == 2 for trace in system.trace)
    reverse_donor_checked = False
    forward_donor_checked = False
    powervalve_effect_checked = False
    for trace in system.trace:
        stage_angles = (trace["angle_start_deg"], trace["angle_end_deg"])
        for stage_state, stage_faces, stage_angle in zip(
                trace["stage_states"][:2], trace["stage_face_fluxes"], stage_angles):
            expected_areas = binding.resolve(system.ducts, stage_angle, 3000.0)
            actual_geometry = trace["stage_geometry"][
                0 if stage_angle == trace["angle_start_deg"] else 1]
            assert actual_geometry["intake_area_m2"] == pytest.approx(expected_areas[0])
            assert actual_geometry["transfer_areas_m2"] == pytest.approx(expected_areas[1])
            assert actual_geometry["exhaust_area_m2"] == pytest.approx(expected_areas[2])
            main_port = next(port for port in ports.ports if port.id == "main-exhaust")
            raw_main_area = ports.area_at(main_port, stage_angle)
            controlled_main_area = valve.area_at(ports, 3000.0, stage_angle)
            if controlled_main_area != pytest.approx(raw_main_area, rel=1e-6, abs=1e-15):
                powervalve_effect_checked = True
            for duct in system.ducts:
                gas_faces = stage_faces[duct.id]["all_faces"]
                species_faces = stage_faces[duct.id]["all_species_faces"]
                cell_species = stage_state["species"]["ducts"][duct.id]
                for face_index in range(1, len(gas_faces) - 1):
                    mass_flux = gas_faces[face_index][0]
                    if mass_flux == 0.0:
                        continue
                    if mass_flux < 0.0:
                        donor = cell_species[face_index]
                        receiver = cell_species[face_index - 1]
                    else:
                        donor = cell_species[face_index - 1]
                        receiver = cell_species[face_index]
                    donor_total = sum(donor)
                    receiver_total = sum(receiver)
                    composition_gap = max(abs(donor[j] / donor_total -
                                              receiver[j] / receiver_total)
                                          for j in range(4))
                    if composition_gap < 1e-4:
                        continue
                    expected_flux = tuple(mass_flux * value / donor_total
                                          for value in donor)
                    assert species_faces[face_index] == pytest.approx(
                        expected_flux, rel=1e-12, abs=1e-15)
                    if mass_flux < 0.0:
                        reverse_donor_checked = True
                    else:
                        forward_donor_checked = True
    assert reverse_donor_checked
    assert forward_donor_checked
    assert powervalve_effect_checked


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


def test_p7_prescribed_combustion_shares_integrated_species_and_energy_stages():
    mass = 1.1768 * .00018
    initial_species = (.00018, .00001, mass - .00019, 0.0)
    system = _case(combustion_start_angle_deg=0.0,
                   cylinder_species=initial_species,
                   transfer_area=0.0, exhaust_area=0.0)
    initial_inventory = system.inventory()
    for _ in range(100):
        record = system.step(.05 / 18000.0, .05)
    assert system.p7_events == []
    final_species = system.state["species"]["chambers"]["cylinder"]
    event = system.p7_event
    assert event is not None
    assert record["stage_p7_source_rates"][0]["heat_w"] > 0.0
    assert record["stage_p7_source_rates"][1]["heat_w"] > 0.0
    assert final_species[0] < initial_species[0]
    assert final_species[1] < initial_species[1]
    assert final_species[3] > 0.0
    assert sum(final_species) == pytest.approx(
        system.state["chambers"]["cylinder"][0], abs=1e-14)
    assert event.ledger.fresh_air_converted == pytest.approx(
        initial_species[0] - final_species[0], abs=1e-14)
    assert event.ledger.fuel_converted == pytest.approx(
        initial_species[1] - final_species[1], abs=1e-14)
    assert system.ledger["p7_heat_added_J"] == pytest.approx(
        800000.0 * event.ledger.burned_produced, rel=1e-12)
    expected_energy_change = (
        system.ledger["external_energy_J"] + system.ledger["p7_heat_added_J"] +
        system.ledger["cylinder_work_J"] + system.ledger["crankcase_work_J"] -
        system.ledger["heat_to_wall_J"])
    assert system.inventory()["energy_J"] - initial_inventory["energy_J"] == pytest.approx(
        expected_energy_change, rel=1e-12, abs=1e-12)
    assert abs(system.conservation_report()["energy"]["residual"]) < 1e-10
    assert abs(system.conservation_report()["mass"]["residual"]) < 1e-14
    assert all(abs(item["residual"]) < 1e-14
               for item in system.conservation_report()["species"].values())


def test_p7_integrated_checkpoint_replays_event_and_rejects_skipped_phase():
    mass = 1.1768 * .00018
    initial_species = (.00018, .00001, mass - .00019, 0.0)
    continuous = _case(combustion_start_angle_deg=0.0,
                       cylinder_species=initial_species,
                       transfer_area=0.0, exhaust_area=0.0)
    for _ in range(60):
        continuous.step(.05 / 18000.0, .05)
    checkpoint = continuous.snapshot()
    expected = continuous.step(.05 / 18000.0, .05)
    replay = _case(combustion_start_angle_deg=0.0,
                   cylinder_species=initial_species,
                   transfer_area=0.0, exhaust_area=0.0)
    replay.restore(checkpoint)
    actual = replay.step(.05 / 18000.0, .05)
    assert replay.state == continuous.state
    assert replay.ledger == continuous.ledger
    assert actual["stage_p7_source_rates"] == expected["stage_p7_source_rates"]
    wrong_contract = _case(cylinder_species=initial_species,
                           transfer_area=0.0, exhaust_area=0.0)
    with pytest.raises(ValueError, match="configuration mismatch"):
        wrong_contract.restore(checkpoint)
    corrupted = deepcopy(checkpoint)
    corrupted["p7"]["active_event"]["start"] = float("nan")
    untouched = _case(combustion_start_angle_deg=0.0,
                      cylinder_species=initial_species,
                      transfer_area=0.0, exhaust_area=0.0)
    before = untouched.snapshot()
    with pytest.raises(ValueError, match="P7 event is invalid"):
        untouched.restore(corrupted)
    assert untouched.snapshot() == before
    skipped = _case(combustion_start_angle_deg=10.0,
                    cylinder_species=initial_species,
                    transfer_area=0.0, exhaust_area=0.0)
    with pytest.raises(ValueError, match="end exactly at ignition"):
        skipped.step(20.0 / 18000.0, 20.0)


def test_p7_ignition_capture_is_transactional_when_the_step_is_rejected():
    mass = 1.1768 * .00018
    initial_species = (.00018, .00001, mass - .00019, 0.0)
    system = _case(combustion_start_angle_deg=10.0,
                   cylinder_species=initial_species,
                   transfer_area=0.0, exhaust_area=0.0)
    system.angle_deg = system.crank_angle_unwrapped_deg = 10.0
    before_state = deepcopy(system.state)
    before_ledger = deepcopy(system.ledger)
    with pytest.raises(ValueError, match="CFL limit exceeded"):
        system.step(1.0, .05)
    assert system.p7_event is None
    assert system.p7_events == []
    assert system.state == before_state
    assert system.ledger == before_ledger
    system.step(.05 / 18000.0, .05)
    assert system.p7_event is not None
    assert system.p7_event.start == pytest.approx(10.0)
    assert system.p7_events == []
    corrupted = system.snapshot()
    corrupted["p7"]["active_event"] = None
    corrupted["p7"]["completed_events"] = []
    corrupted["ledger"]["p7_heat_added_J"] = 0.0
    corrupted["ledger"]["p7_source_species_kg"] = [0.0] * 4
    target = _case(combustion_start_angle_deg=10.0,
                   cylinder_species=initial_species,
                   transfer_area=0.0, exhaust_area=0.0)
    with pytest.raises(ValueError, match="missing the event"):
        target.restore(corrupted)


def test_p7_event_boundary_requires_exact_alignment_and_stops_cleanly():
    mass = 1.1768 * .00018
    initial_species = (.00018, .00001, mass - .00019, 0.0)
    system = _case(combustion_start_angle_deg=0.0,
                   cylinder_species=initial_species,
                   transfer_area=0.0, exhaust_area=0.0, duct_length=.2)
    def advance_to(target):
        while system.crank_angle_unwrapped_deg < target - 1e-12:
            delta = min(.05, target - system.crank_angle_unwrapped_deg)
            while True:
                try:
                    system.step(delta / 18000.0, delta)
                    break
                except ValueError as error:
                    if "inadmissible species mass" not in str(error):
                        raise
                    delta /= 2.0
                    assert delta > 1e-7
    advance_to(39.95)
    before_state = deepcopy(system.state)
    before_angle = system.crank_angle_unwrapped_deg
    before_heat = system.ledger["p7_heat_added_J"]
    with pytest.raises(ValueError, match="event boundary"):
        system.step(.1 / 18000.0, .1)
    assert system.state == before_state
    assert system.crank_angle_unwrapped_deg == before_angle
    assert system.ledger["p7_heat_added_J"] == before_heat
    advance_to(40.0)
    assert system.crank_angle_unwrapped_deg == pytest.approx(40.0)
    assert system.trace[-1]["stage_p7_source_rates"][1]["heat_w"] == pytest.approx(0.0)
