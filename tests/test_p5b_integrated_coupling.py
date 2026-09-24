import pytest
from unittest.mock import patch

from motorsim.p5b import (
    Chamber,
    IntegratedIntakeTransfer,
    make_single_0d1d_fixture,
    interior_rhs,
    make_closed_volume_work_fixture,
    ssprk2_step,
)
from motorsim.gas1d.mesh import uniform_mesh
from motorsim.gas1d.boundary import Boundary
from motorsim.gas1d.eos import IdealGas
from motorsim import p5b

E=IdealGas()
def make():
    c=Chamber((1.0,0.,100000.,.5),.001); y=Chamber((1.0,0.,100000.,.5),.01)
    duct=(1.0,0.,101325.,0.)
    return IntegratedIntakeTransfer(c,y,(duct,duct,duct),eos=E)

def test_stage_port_events_and_closed_leakage():
    n=make(); h=n.step(.01, angle=0); assert h['areas']==(0.,0.,0.)
    h=n.step(.01, angle=300); assert h['areas'][0]>0

def test_two_transfer_entities_and_restart_determinism():
    a=make(); a.step(.01,angle=120); snap=a.snapshot(); a.step(.01,angle=250)
    b=make(); b.restore(snap); b.step(.01,angle=250)
    assert a.history[-1] == b.history[-1]

def test_complete_subsystem_has_trace_and_no_exhaust():
    n=make(); [n.step(.005, angle=i*30) for i in range(12)]
    assert len(n.history)==12 and all(len(x['fluxes'])==3 for x in n.history)

def test_interior_rhs_uses_gas1d_hllc():
    mesh=uniform_mesh(2, length=1., area=1.)
    states=[(1.,0.,100000.,.2),(1.,10.,100000.,.2)]
    rhs=interior_rhs(mesh,states,E)
    assert len(rhs)==2 and rhs[0][0] != 0

def test_global_ssprk2_two_stages():
    out=ssprk2_step((1.,), lambda z:(-z[0],), .1)
    assert 0 < out[0] < 1

def test_chamber_rhs_sums_one_stage_and_includes_volume_work():
    chamber = Chamber((2.0, 0.0, 100000.0, .25), .01)
    rhs = chamber.conservative_rhs(
        ((.2, 0.0, 10.0, .05), (-.1, 0.0, -4.0, -.02)),
        E, volume_rate=.003)
    assert rhs[0] == .1
    assert abs(rhs[1] - (6.0 - 100000.0*.003)) < 1e-12
    assert abs(rhs[2] - .03) < 1e-12

def test_chamber_stage_updates_volume_and_uses_pre_stage_pressure():
    chamber = Chamber((2.0, 0.0, 100000.0, .25), .01)
    initial = chamber.inventory(E)
    rhs = chamber.conservative_rhs(((0.0, 0.0, 0.0, 0.0),), E,
                                   volume_rate=.001)
    chamber.apply_rhs(rhs, .1, E, volume_rate=.001)
    assert chamber.volume == .0101
    assert chamber.inventory(E)[0] == initial[0]
    assert chamber.inventory(E)[2] < initial[2]

def test_integrated_step_applies_each_chamber_once_with_volume_work():
    n = make()
    n.volume_rates = (.001, -.0005)
    n.step(.01, angle=120)
    assert n.crankcase.volume == .00101
    assert n.cylinder.volume == .009995
    assert n.ledger['cc_work'] < 0
    assert n.ledger['cyl_work'] > 0

def test_contractual_volume_work_uses_stage_pressure_and_sign():
    chamber = Chamber((2.0, 0.0, 100000.0, .01), .01)
    initial = chamber.inventory(E)
    volume_rate = .001
    dt = .1
    rhs = chamber.conservative_rhs(((0.0, 0.0, 0.0, 0.0),), E,
                                   volume_rate=volume_rate)
    chamber.apply_rhs(rhs, dt, E, volume_rate=volume_rate)

    # The contractual source is -p_stage*dV/dt.  No interface flux means
    # mass/species stay fixed while expansion removes exactly p*dV energy.
    assert chamber.volume == .0101
    assert chamber.inventory(E)[0] == initial[0]
    assert chamber.inventory(E)[1] == initial[1]
    assert chamber.inventory(E)[2] == initial[2] - 100000.0*volume_rate*dt

def test_contractual_volume_work_compression_has_opposite_sign():
    chamber = Chamber((2.0, 0.0, 100000.0, .01), .01)
    initial = chamber.inventory(E)
    volume_rate = -.001
    dt = .1
    rhs = chamber.conservative_rhs(((0.0, 0.0, 0.0, 0.0),), E,
                                   volume_rate=volume_rate)
    chamber.apply_rhs(rhs, dt, E, volume_rate=volume_rate)
    assert chamber.volume == .0099
    assert chamber.inventory(E)[2] == initial[2] + 100000.0*.001*dt

def test_contractual_volume_work_rejects_nonfinite_inputs():
    chamber = Chamber((2.0, 0.0, 100000.0, .01), .01)
    with pytest.raises(ValueError):
        chamber.conservative_rhs(((0.0, 0.0, 0.0, 0.0),), E, volume_rate=float('nan'))
    with pytest.raises(ValueError):
        chamber.apply_rhs((0.0, 0.0, float('inf')), .1, E)

def test_each_interface_is_resolved_once_from_its_own_duct_state():
    node = make()
    calls = []
    expected_interiors = [duct.primitive(E) for duct in node.duct_states]
    from motorsim import p5b
    original = p5b.interface_exchange

    def audited(chamber, interior, area, normal, *, eos):
        result = original(chamber, interior, area, normal, eos=eos)
        calls.append((interior, area, normal, tuple(result['outward'])))
        return result

    with patch.object(p5b, 'interface_exchange', side_effect=audited):
        history = node.step(.01, angle=150)

    assert len(calls) == 3
    assert calls[0][0] == expected_interiors[0]
    assert calls[1][0] == expected_interiors[1]
    assert calls[2][0] == expected_interiors[2]
    assert tuple(history['fluxes']) == tuple(call[3] for call in calls)


def test_mass_global_ledger_balances_external_intake_and_internal_transfers():
    node = make()
    initial = node.mass_ledger()
    assert initial['delta_mass'] == 0.0
    assert initial['external_mass'] == 0.0
    assert initial['residual'] == 0.0

    for angle in (0.0, 120.0, 150.0, 300.0, 330.0):
        node.step(.001, angle=angle)

    audit = node.mass_ledger()
    assert audit['external_mass'] > 0.0
    assert audit['delta_mass'] == pytest.approx(audit['external_mass'], abs=1e-15)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-15)


def test_mass_global_ledger_is_closed_when_all_ports_are_closed():
    node = make()
    for angle in (0.0, 30.0, 60.0, 240.0):
        node.step(.001, angle=angle)

    audit = node.mass_ledger()
    assert audit['external_mass'] == 0.0
    assert audit['delta_mass'] == pytest.approx(0.0, abs=1e-15)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-15)

def test_species_global_ledger_balances_external_intake_and_internal_transfers():
    # Use a pressure-high crankcase so the open intake carries the chamber's
    # passive species out through the external boundary.
    node = IntegratedIntakeTransfer(
        Chamber((1.0, 0.0, 110000.0, .5), .001),
        Chamber((1.0, 0.0, 100000.0, .5), .01),
        ((1.0, 0.0, 101325.0, 0.0),) * 3,
        eos=E,
    )
    initial = node.species_ledger()
    assert initial['delta_species'] == 0.0
    assert initial['external_species'] == 0.0
    assert initial['residual'] == 0.0

    for angle in (0.0, 120.0, 150.0, 300.0, 330.0):
        node.step(.001, angle=angle)

    audit = node.species_ledger()
    # The signed boundary convention is shared with the mass ledger; this
    # fixture's prescribed atmosphere has Y=0, so species leaves the chamber
    # during the intake-open interval and the signed value is negative.
    assert abs(audit['external_species']) > 0.0
    assert audit['delta_species'] == pytest.approx(audit['external_species'], abs=1e-15)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-15)

def test_species_global_ledger_is_closed_when_all_ports_are_closed():
    node = make()
    for angle in (0.0, 30.0, 60.0, 240.0):
        node.step(.001, angle=angle)

    audit = node.species_ledger()
    assert audit['external_species'] == 0.0
    assert audit['delta_species'] == pytest.approx(0.0, abs=1e-15)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-15)


def test_species_global_ledger_cancels_internal_transfers_and_tracks_external_port():
    node = make()
    initial = node.species_ledger()
    assert initial['delta_species'] == 0.0
    assert initial['external_species'] == 0.0
    assert initial['residual'] == 0.0

    for angle in (120.0, 150.0, 300.0, 330.0):
        node.step(.001, angle=angle)

    audit = node.species_ledger()
    assert audit['external_species'] == pytest.approx(0.0, abs=1e-15)
    assert audit['delta_species'] == pytest.approx(audit['external_species'], abs=1e-15)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-15)


def test_energy_global_ledger_conserves_fixed_volume_closed_internal_system():
    node = make()
    initial = node.energy_ledger()
    assert initial['delta_energy'] == 0.0
    for angle in (0.0, 30.0, 60.0, 240.0):
        node.step(.001, angle=angle)

    audit = node.energy_ledger()
    assert audit['external_energy'] == 0.0
    assert audit['chamber_work'] == 0.0
    assert audit['delta_energy'] == pytest.approx(0.0, abs=1e-12)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-12)


def test_energy_global_ledger_tracks_external_boundary_flux_once():
    node = make()
    node.step(.001, angle=300.0)

    audit = node.energy_ledger()
    assert audit['external_energy'] != 0.0
    assert audit['cc_work'] == 0.0
    assert audit['cyl_work'] == 0.0
    assert audit['delta_energy'] == pytest.approx(audit['external_energy'], abs=2e-12)
    assert audit['residual'] == pytest.approx(0.0, abs=2e-12)


def test_energy_global_ledger_preserves_variable_volume_work_signs():
    node = make()
    node.volume_rates = (.001, -.0005)
    node.step(.001, angle=0.0)

    audit = node.energy_ledger()
    assert audit['external_energy'] == 0.0
    assert audit['cc_work'] < 0.0
    assert audit['cyl_work'] > 0.0
    assert audit['delta_energy'] == pytest.approx(audit['chamber_work'], abs=1e-12)
    assert audit['residual'] == pytest.approx(0.0, abs=1e-12)


def test_closed_volume_work_fixture_conserves_inventories_and_has_no_flux():
    node = make_closed_volume_work_fixture()
    initial_mass = node.mass_ledger()['initial_mass']
    initial_species = node.species_ledger()['initial_species']
    initial_energy = node.energy_ledger()['initial_energy']

    for angle in (0.0, 30.0, 60.0, 240.0) * 5:
        trace = node.step(1.0e-3, angle=angle)
        assert trace['areas'] == (0.0, 0.0, 0.0)
        assert all(all(value == 0.0 for value in flux) for flux in trace['fluxes'])

    mass = node.mass_ledger()
    species = node.species_ledger()
    energy = node.energy_ledger()
    assert mass['final_mass'] == pytest.approx(initial_mass, abs=1e-15)
    assert species['final_species'] == pytest.approx(initial_species, abs=1e-15)
    assert mass['external_mass'] == 0.0 and mass['residual'] == pytest.approx(0.0, abs=1e-15)
    assert species['external_species'] == 0.0 and species['residual'] == pytest.approx(0.0, abs=1e-15)
    assert energy['external_energy'] == 0.0
    assert energy['delta_energy'] == pytest.approx(energy['chamber_work'], abs=1e-12)
    assert energy['residual'] == pytest.approx(0.0, abs=1e-12)
    assert energy['cc_work'] > 0.0
    assert energy['cyl_work'] < 0.0
    assert energy['final_energy'] == pytest.approx(initial_energy + energy['chamber_work'], abs=1e-12)


def test_closed_volume_work_fixture_keeps_chambers_admissible():
    node = make_closed_volume_work_fixture(volume_rates=(-2.0e-4, 2.0e-4))
    for angle in (0.0, 60.0, 240.0) * 4:
        node.step(1.0e-3, angle=angle)
        for chamber in (node.crankcase, node.cylinder):
            rho, pressure, temperature, fraction = chamber.thermodynamics(E)
            assert rho > 0.0 and pressure > 0.0 and temperature > 0.0
            assert 0.0 <= fraction <= 1.0


def test_single_0d1d_fixture_is_finite_and_externally_closed():
    node = make_single_0d1d_fixture(cells=3)
    initial = node.conservation()["initial"]
    for _ in range(8):
        node.step(1.0e-7)
    audit = node.conservation()
    assert audit["final"]["mass"] == pytest.approx(initial["mass"], abs=1.0e-15)
    assert audit["final"]["energy"] == pytest.approx(initial["energy"], abs=1.0e-10)
    assert audit["final"]["species"] == pytest.approx(initial["species"], abs=1.0e-15)
    assert all(abs(value) < 1.0e-10 for value in audit["delta"].values())
    assert node.admissible()


def test_single_0d1d_fixture_reuses_one_shared_flux_with_opposite_signs():
    node = make_single_0d1d_fixture(cells=1)
    trace = node.step(1.0e-7)
    for stage, shared in enumerate(trace["shared_fluxes"]):
        chamber_rhs = trace["chamber_rhs"][stage]
        duct_rhs = trace["duct_rhs"][stage][0]
        assert chamber_rhs[0] == shared[0]
        assert chamber_rhs[2] == shared[2]
        assert chamber_rhs[3] == shared[3]
        assert duct_rhs[0] == pytest.approx(-shared[0] / node.mesh.volumes[0])
        assert duct_rhs[2] == pytest.approx(-shared[2] / node.mesh.volumes[0])
        assert duct_rhs[3] == pytest.approx(-shared[3] / node.mesh.volumes[0])
    assert any(abs(value) > 0.0 for value in trace["shared_fluxes"][0])


def test_single_0d1d_fixture_keeps_chamber_volume_fixed_and_admissible():
    node = make_single_0d1d_fixture()
    volume = node.chamber.volume
    for _ in range(5):
        node.step(1.0e-7)
    rho, pressure, temperature, fraction = node.chamber.thermodynamics(E)
    assert node.chamber.volume == volume
    assert rho > 0.0 and pressure > 0.0 and temperature > 0.0
    assert 0.0 <= fraction <= 1.0
    assert node.admissible()


def test_single_0d1d_fixture_uses_contractual_rigid_wall_momentum_flux():
    node = make_single_0d1d_fixture(cells=1)
    state = node._state()
    (rhs, shared, _) = node._rhs(state)
    wall = Boundary('wall').flux(E.primitive(state[1][0]), 1, E)[0]
    assert wall[0] == 0.0 and wall[2] == 0.0 and wall[3] == 0.0
    assert wall[1] > 0.0
    expected = -(node.mesh.areas[-1] * wall[1] - (-shared[1])) / node.mesh.volumes[0]
    assert rhs[1][0][1] == pytest.approx(expected)


def test_single_0d1d_fixture_validates_chamber_as_extensive_inventory():
    eos = IdealGas()
    node = make_single_0d1d_fixture(eos=eos, cells=1)
    state = node._state()
    calls = []
    chamber_state = p5b.ChamberState

    def record_chamber_state(*args):
        calls.append(args)
        return chamber_state(*args)

    with patch.object(p5b, 'ChamberState', side_effect=record_chamber_state):
        node._validate_state(state)

    assert calls == [(
        state[0][0],
        state[0][2],
        state[0][3],
        node.chamber.volume,
    )]
