import pytest

from motorsim.p5b import Chamber, IntegratedIntakeTransfer, interior_rhs, ssprk2_step
from motorsim.gas1d.mesh import uniform_mesh
from motorsim.gas1d.eos import IdealGas

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
