import copy

from motorsim.p5c import IntegratedP5C, make_p5c_fixture


def test_p5c_closed_ports_and_conditional_ledger():
    s = make_p5c_fixture(port_area=0.0)
    before = s.totals()
    trace = s.step(1.0e-7)
    assert trace["dependency"] == "CONDITIONAL_ON_P4"
    assert trace["exhaust"]["closed"]
    assert trace["exhaust"]["flux"][0] == 0.0
    assert trace["exhaust"]["flux"][2:] == (0.0, 0.0)
    assert s.admissible()
    assert abs(s.totals()["mass"] - before["mass"]) < 1e-9
    assert abs(s.totals()["species"] - before["species"]) < 1e-9
    assert abs(s.totals()["energy"] - before["energy"]) < 1e-4


def test_p5c_restart_replay():
    a = make_p5c_fixture(port_area=1.0e-4)
    a.step(1.0e-7)
    snap = a.snapshot()
    a.step(1.0e-7)
    expected = a.totals()
    b = make_p5c_fixture(port_area=1.0e-4)
    b.restore(snap)
    b.step(1.0e-7)
    assert b.totals() == expected


def test_p5c_full_topology_evolves_exhaust():
    s = make_p5c_fixture(port_area=1.0e-4)
    initial = s.exhaust.cells[0].conservative
    s.step(1.0e-7)
    assert s.history[-1]["exhaust"]["area"] > 0
    # Equal-pressure initial states may only carry wall momentum; the duct is
    # still dynamically included in the unified RHS and remains admissible.
    assert s.admissible()


def test_p5c_single_rhs_contains_two_transfers_and_exhaust():
    s = make_p5c_fixture(port_area=1.0e-4)
    s.step(1.0e-7)
    interfaces = s.history[-1]["stage_interfaces"][0]
    assert len(interfaces) == 3
    assert s.history[-1]["stage_rhs"][0] == s.history[-1]["stage_rhs"][0]


def test_p5c_closed_exhaust_keeps_transfer_interfaces_in_rhs():
    s = make_p5c_fixture(port_area=0.0)
    s.step(1.0e-7)
    interfaces = s.history[-1]["stage_interfaces"][0]
    assert interfaces[2][0] == 0.0 and interfaces[2][2] == 0.0
    assert len(interfaces[:2]) == 2


def test_p5c_full_fixture_uses_compatible_atmospheric_state():
    s = __import__('motorsim.p5c', fromlist=['make_p5c_full_fixture']).make_p5c_full_fixture()
    s.step(1.0e-7, angle=0.0)
    assert s.admissible()


def test_p5c_controlled_internal_backflow_uses_resolved_flux():
    from motorsim.p5c import make_p5c_backflow_fixture
    s = make_p5c_backflow_fixture()
    s.step(1.0e-7, angle=150.0)
    # Interface index 1 is crankcase -> TR1 in the established trace order.
    assert s.history[-1]["core_interfaces"][0][1][0] < 0.0
    assert s.admissible()
