import math
from motorsim.duct_network import DuctGeometry, NetworkState, PortInterface, interface_exchange, volume_of_segment
from motorsim.project import DuctSegment
from motorsim.gas1d.eos import IdealGas


def test_geometry_and_exact_frustum_volume():
    g = DuctGeometry("intake", (DuctSegment("s", 100, 20, 20),), "external_to_crankcase")
    assert g.mesh(.02).n == 5
    assert math.isclose(volume_of_segment(100, 20, 20), math.pi*.1*.02**2/4)


def test_port_laws_and_closed_port():
    p = PortInterface(10, 20, 0)
    assert p.transfer_area(0) == 0
    assert p.transfer_area(10) == 100
    assert p.transfer_area(30) == 200
    closed = interface_exchange(None, None, 0, -1)
    assert closed["outward"] == (0.0, 0.0, 0.0, 0.0)


def test_topology_keeps_transfers_independent():
    a = DuctGeometry("t1", (DuctSegment("s", 50, 10, 10),), "crankcase_to_cylinder")
    b = DuctGeometry("t2", (DuctSegment("s", 60, 10, 12),), "crankcase_to_cylinder")
    network = NetworkState(transfers=(a, b))
    assert network.transfers[0] != network.transfers[1]


def test_state_validation_has_no_clipping():
    eos = IdealGas()
    assert eos.validate((1.0, 0.0, 100000.0, .5))[0] == 1.0
