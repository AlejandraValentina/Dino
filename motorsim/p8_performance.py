"""P8 bounded transient driver using the existing physical-time CFL contract."""
from dataclasses import dataclass, replace
from math import pi, isfinite
import csv, json
from pathlib import Path
from .project import ProjectError
from .gas1d.solver import cfl_step, event_step

RPM_MIN,RPM_MAX=2500,15000; P8_ANCHORS=(2500,5000,8000,11000,15000); P8_CFL=.4
def validate_p8_rpm(rpm):
    if type(rpm) is not int or not RPM_MIN<=rpm<=RPM_MAX: raise ProjectError(f'P8 RPM must be an integer in [{RPM_MIN}, {RPM_MAX}]')
    return rpm
def omega_deg_s(rpm): return 6.0*validate_p8_rpm(rpm)
def cycle_duration_s(rpm): return 60.0/validate_p8_rpm(rpm)
def indicated_metrics(work_j,rpm,pmax_pa):
    validate_p8_rpm(rpm)
    if not all(isfinite(float(x)) for x in (work_j,pmax_pa)): raise ValueError('P8 metrics must be finite')
    return {'W_cycle_J':float(work_j),'P_indicated_W':float(work_j)*rpm/60.0,'T_indicated_Nm':float(work_j)/(2*pi),'p_max_Pa':float(pmax_pa)}
def work_from_pressure_volume(p,v):
    if len(p)!=len(v) or len(p)<2: raise ValueError('pressure and volume paths must have equal length >= 2')
    return sum(.5*(a+b)*(d-c) for a,b,c,d in zip(p,p[1:],v,v[1:]))
@dataclass(frozen=True)
class P8Semantics:
    contract_version:str='P8-WIDE-RPM-TRANSIENT-V1'; steady_state:bool=False; periodic_convergence:str='NOT_GRANTED_BY_P4'; metric_semantics:str='BOUNDED_TRANSIENT_INDICATED'; conditional_on_p4:bool=True; experimental_validation:str='NOT_PERFORMED'; independent_review:str='INDEPENDENT_REVIEW_PENDING'
def model_geometry_callback(model):
    def callback(angle):
        volumes,rates,areas=model.geometry(float(angle)); return {'volumes':volumes,'volume_rates':(rates[1],rates[2]),'areas':(areas[1],areas[2],areas[3],areas[4])}
    return callback
def _new_system(rpm):
    from .simulation_case import SyntheticCase
    from .simulation import Model
    from .p5c import make_p5c_full_fixture
    from .p6_species import P6IntegratedSystem
    from .gas1d.eos import IdealGas
    from .p6_species import legacy_to_species
    case=replace(SyntheticCase(),rpm=rpm); model=Model(case,external_band_pa=100); gas=make_p5c_full_fixture(eos=IdealGas(R=287,gamma=1.35),cells=2); gas.geometry_callback=model_geometry_callback(model); gas.core.geometry_callback=gas.geometry_callback; gas.angle=case.initial_angle_deg
    volumes=model.geometry(180)[0]
    for chamber,pty,volume in ((gas.core.crankcase,case.initial_pty[1],volumes[1]),(gas.core.cylinder,case.initial_pty[2],volumes[2])):
        p,t,marker=pty; chamber.volume=volume; chamber.primitive=(p/(gas.eos.R*t),0.0,p,float(marker))
    gas.core._initial=gas.core._totals(); gas._initial=gas.totals(); gas._previous_totals=dict(gas._initial)
    def mapped(mass, marker):
        values=legacy_to_species(mass,float(marker)); return tuple(x/mass for x in values)
    species={'crankcase':[mapped(gas.core.crankcase.inventory(gas.eos)[0],1)],'cylinder':[mapped(gas.core.cylinder.inventory(gas.eos)[0],0)]}
    for name,path in [('intake',gas.core.intake),('tr1',gas.core.transfers[0]),('tr2',gas.core.transfers[1]),('exhaust',gas.exhaust)]:
        species[name]=[mapped(q[0]*v,q[3]/q[0]) for q,v in zip(path.conservative(),path.mesh.volumes)]
    return case,P6IntegratedSystem(gas,component_species=species,capture_trace=True,enable_p7=True,angular_rate_deg_s=omega_deg_s(rpm))
def _cfl_dt(gas):
    limits=[]
    for path in (gas.core.intake,*gas.core.transfers,gas.exhaust):
        states=[gas.eos.primitive(q) for q in path.conservative()]; speeds=[abs(w[1])+gas.eos.sound_speed(w) for w in states]; speeds=[speeds[0],*[max(a,b) for a,b in zip(speeds,speeds[1:])],speeds[-1]]
        dt,_,unit=cfl_step(path.mesh,states,speeds,gas.eos,P8_CFL); limits.append((dt,unit))
    return min(limits)
def _step_dt(gas, rpm, end, cuts):
    """Return the next physical-time step for every continuation path.

    Event/port cuts are part of the integration contract, not just a detail
    of the uninterrupted driver.  Keeping this calculation shared makes a
    restored run reproduce the exact timestep partition of its original run.
    """
    cfl_dt,_=_cfl_dt(gas)
    remaining=(end-gas.angle)/omega_deg_s(rpm)
    dt=event_step(cfl_dt,remaining)
    nxt=next((x for x in cuts if x>gas.angle+1e-12),end)
    return min(dt,(nxt-gas.angle)/omega_deg_s(rpm)),cfl_dt
def _run_once(rpm):
    case,system=_new_system(rpm); gas=system.gas; start=float(gas.angle); end=start+360.; dts=[]; cfls=[]; checkpoint=None
    from .coupling import ChamberState
    from .simulation import Model
    cuts=sorted({float(x) for x in Model(case).events+[350,390,540] if start < x <= end})
    while gas.angle<end-1e-12:
        dt,cfl_dt=_step_dt(gas,rpm,end,cuts)
        if checkpoint is None and 370<=gas.angle<390: checkpoint=system.snapshot()
        system.step(dt,angle=gas.angle+dt*omega_deg_s(rpm)); dts.append(dt); cfls.append(dt/(cfl_dt/P8_CFL))
    if checkpoint is None: raise RuntimeError('restart checkpoint was not reached inside P7 event')
    def pressure(q): return ChamberState(q[0],q[2],q[3],q[4]).thermodynamics(gas.eos)[1]
    pmax=max((pressure(h['stage_states'][i][1]) for h in gas.history for i in range(3)),default=0.0)
    work=-sum(.5*h['dt']*sum(h['stage_work_rates'][i][1] for i in (0,1)) for h in gas.history); ccwork=-sum(.5*h['dt']*sum(h['stage_work_rates'][i][0] for i in (0,1)) for h in gas.history); system.validate(); gas.admissible(); ledger=system.p7_event.ledger
    final=gas.totals(); ext=gas._external_cumulative; eres=final['energy']-gas._initial['energy']-ext['energy']-sum(h['prescribed_heat'] for h in gas.history)+work+ccwork; mres=final['mass']-gas._initial['mass']-ext['mass']
    r={'rpm':rpm,'omega_deg_s':omega_deg_s(rpm),'window_deg':[start,end],'window_s':cycle_duration_s(rpm),'step_count':len(dts),'actual_dt_min_s':min(dts),'actual_dt_max_s':max(dts),'achieved_CFL_min':min(cfls),'achieved_CFL_max':max(cfls),'cfl_contract':P8_CFL,**indicated_metrics(work,rpm,pmax),'prescribed_heat_J':ledger.heat_added,'fresh_mass_delivered_kg':system.fresh_delivered,'fresh_short_circuit_mass_kg':system.fresh_short_circuit,'species_residual_kg':system.species_sum_error(),'global_mass_residual_kg':mres,'global_energy_residual_J':eres,'delivered_work_crankcase_J':ccwork,'inventory':system.inventory_snapshot(),'species_mass':system.species_mass,'p7_ledger':vars(ledger).copy()}
    r['gates']={'finite':all(isfinite(float(x)) for x in (work,pmax,*dts,*cfls)),'admissible':bool(gas.admissible()),'species':abs(system.species_sum_error())<1e-12,'p7_one_event':len(system.p7_events)==1,'p7_source_admissible':abs(ledger.source_mass_residual)<1e-14 and ledger.burned_produced<=system.p7_event.fresh+1e-12,'p7_heat_consistent':abs(ledger.heat_burn_residual)<1e-10,'cfl':max(cfls)<=P8_CFL+1e-12}
    _,restored=_new_system(rpm); restored.restore(checkpoint)
    while restored.gas.angle<end-1e-12:
        step,_=_step_dt(restored.gas,rpm,end,cuts); restored.step(step,angle=restored.gas.angle+step*omega_deg_s(rpm))
    def current(s): return (s.gas.angle,s.gas._state(),s.species_mass,s._external)
    r['restart']={'executed':True,'state_equal':current(restored)==current(system),'species_mass_equal':restored.species_mass==system.species_mass,'p7_ledger_equal':vars(restored.p7_event.ledger)==vars(system.p7_event.ledger),'external_equal':restored._external==system._external,'fresh_delivery_equal':restored.fresh_delivered==system.fresh_delivered,'short_circuit_equal':restored.fresh_short_circuit==system.fresh_short_circuit}; r['gates']['restart']=all(r['restart'].values()); return r
def run_anchor(rpm,**kwargs):
    a=_run_once(rpm); b=_run_once(rpm); a['deterministic_replay']={'executed':True,'state_equal':a['inventory']==b['inventory'] and a['species_mass']==b['species_mass'],'species_mass_equal':a['species_mass']==b['species_mass'],'p7_ledger_equal':a['p7_ledger']==b['p7_ledger'],'metrics_equal':all(abs(a[k]-b[k])<=1e-12*max(1,abs(a[k])) for k in ('W_cycle_J','p_max_Pa','P_indicated_W','T_indicated_Nm'))}; a['gates']['deterministic_replay']=all(a['deterministic_replay'].values()); return a
def run_campaign(output_dir):
    from .simulation_case import SyntheticCase
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); anchors=[run_anchor(r) for r in P8_ANCHORS]; failures=[f"{a['rpm']}:{k}" for a in anchors for k,v in a['gates'].items() if not v]; ok=not failures; payload={'status':'P8_WIDE_RPM_PERFORMANCE_VERIFIED_CONDITIONAL' if ok else 'P8_NUMERICAL_GATE_BLOCKED','closure':'P8_READY_FOR_P9_DATA' if ok else 'P8_NUMERICAL_GATE_BLOCKED','failures':failures,'semantics':vars(P8Semantics()),'provenance':{'mechanics':'S2T-0D-01','initial_angle_deg':180,'initial_states_pty':SyntheticCase().initial_pty,'intake_reservoir':'P5-C 101325 Pa / 300 K','exhaust_boundary':'P5-C outflow','topology':'frozen P5-C/P6/P7 full-topology fixture','synthetic_not_measured':True},'p4':'BLOCKED / NOT_GRANTED','anchors':anchors}; (output_dir/'p8-wide-rpm.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); fields=['rpm','window_s','step_count','actual_dt_min_s','actual_dt_max_s','achieved_CFL_min','achieved_CFL_max','W_cycle_J','P_indicated_W','T_indicated_Nm','p_max_Pa'];
    with (output_dir/'p8-wide-rpm.csv').open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:a[k] for k in fields} for a in anchors)
    return payload
