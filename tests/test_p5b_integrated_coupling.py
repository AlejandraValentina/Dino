from motorsim.p5b import Chamber, IntegratedIntakeTransfer
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
