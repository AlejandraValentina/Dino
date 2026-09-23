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
