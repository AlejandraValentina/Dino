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
    assert s.exhaust.cells[0].conservative != initial
