"""P2A only: first-order finite volume / Forward Euler. Standard-library float64."""
from math import fsum, isfinite
import time
from .eos import IdealGas,InvalidState
from .riemann import hllc_flux


def inventories(cells):return [fsum(c[k] for c in cells) for k in range(4)]


def cfl_step(mesh, states, speeds, eos, cfl):
    if not isfinite(cfl) or not 0<cfl<=.6:raise ValueError('Contractual CFL outside (0,.6]')
    limits=[]
    for i,(w,v,dx) in enumerate(zip(states,mesh.volumes,mesh.widths)):
        limits.append(min(dx/(abs(w[1])+eos.sound_speed(w)),
                          2*v/(mesh.areas[i]*speeds[i]+mesh.areas[i+1]*speeds[i+1])))
    index=min(range(mesh.n),key=limits.__getitem__)
    return cfl*limits[index],index,limits[index]


def solve(mesh, initial, final_time, boundaries, *, eos=None, cfl=.4,
          sample_interval=None, sensor=None, wall_limit=120., progress=None):
    eos=eos or IdealGas();started=time.monotonic()
    cells=[tuple(q) for q in initial]
    if len(cells)!=mesh.n or not isfinite(final_time) or final_time<=0:raise ValueError('Invalid initial mesh/time')
    def primitive(c):return [eos.primitive(tuple(x/v for x in row)) for row,v in zip(c,mesh.volumes)]
    states=primitive(cells);initial_inventory=inventories(cells)
    boundary_int=[0.]*4;source_int=[0.]*4;boundary_abs=[0.]*4;source_abs=[0.]*4
    initial_abs=[fsum(abs(c[k]) for c in cells) for k in range(4)]
    a0=eos.sound_speed(states[0]);scales=[initial_inventory[0],initial_inventory[0]*a0,initial_inventory[2],initial_inventory[0]]
    periodic=boundaries=='periodic'
    if periodic and mesh.areas[0]!=mesh.areas[-1]:raise ValueError('Periodic faces must share area')
    t=0.;step=0;rejections=0;fallbacks={};hllc_count=0;minimum_dt=None;max_cfl=0.;history=[];signals=[];fallback_records=[]
    extrema=[min(w[0] for w in states),min(w[2] for w in states),min(w[2]/(w[0]*eos.R) for w in states),min(w[3] for w in states),max(w[3] for w in states),max(abs(w[1])/eos.sound_speed(w) for w in states)]
    status='completed';reason='final_time';fluxes=[];next_sample=sample_interval;sample_number=1
    def observe_sensor():
        if sensor is not None:
            from bisect import bisect_right
            j=max(0,min(mesh.n-2,bisect_right(mesh.centers,sensor)-1));xl,xr=mesh.centers[j:j+2]
            signals.append([t,states[j][2]+(states[j+1][2]-states[j][2])*(sensor-xl)/(xr-xl)])
    observe_sensor()
    while t<final_time:
        if time.monotonic()-started>wall_limit:status='failed_infrastructure';reason='wall_timeout';break
        try:
            data=[hllc_flux(a,b,eos) for a,b in zip(states,states[1:])]
            if periodic:
                face=hllc_flux(states[-1],states[0],eos);data=[face,*data,face]
            else:data=[boundaries[0].flux(states[0],-1,eos),*data,boundaries[1].flux(states[-1],1,eos)]
            fluxes=[tuple(a*f for f in item[0]) for a,item in zip(mesh.areas,data)]
            speeds=[max(abs(d[1][0]),abs(d[1][2])) for d in data]
            for i,d in enumerate(data):
                if d[2]:
                    fallbacks[d[2]]=fallbacks.get(d[2],0)+1
                    if len(fallback_records)<100:fallback_records.append(dict(step=step,face=i,reason=d[2],speeds=d[1],left=states[max(0,i-1)],right=states[min(mesh.n-1,i)]))
                else:hllc_count+=1
            dt,limiting,dt_unit=cfl_step(mesh,states,speeds,eos,cfl)
            dt=min(dt,final_time-t)
            if next_sample is not None:dt=min(dt,next_sample-t)
            source=[w[2]*(mesh.areas[i+1]-mesh.areas[i]) for i,w in enumerate(states)]
            delta=[tuple(fluxes[i][k]-fluxes[i+1][k]+(source[i] if k==1 else 0.) for k in range(4)) for i in range(mesh.n)]
            accepted=False
            for retry in range(13):
                if dt<1e-12 or t+dt==t:
                    if final_time-t<=16*2.220446049250313e-16*max(1.,abs(final_time)):
                        t=final_time;accepted=True;dt=0.;break
                    raise InvalidState('dt_below_min')
                candidate=[tuple(a+dt*b for a,b in zip(c,d)) for c,d in zip(cells,delta)]
                try:new_states=primitive(candidate)
                except InvalidState:
                    rejections+=1
                    if retry==12:raise InvalidState('admissibility_retries_exhausted')
                    dt/=2;continue
                accepted=True;break
            if dt==0:break
            if not accepted:raise InvalidState('step_rejected')
        except (InvalidState,OverflowError,ZeroDivisionError) as exc:
            status='failed_numerical';reason=str(exc);break
        cells=candidate;states=new_states;t+=dt;step+=1
        minimum_dt=dt if minimum_dt is None else min(minimum_dt,dt);max_cfl=max(max_cfl,dt/dt_unit)
        for k in range(4):
            boundary_int[k]+=dt*(fluxes[-1][k]-fluxes[0][k])
            boundary_abs[k]+=dt*(abs(fluxes[-1][k])+abs(fluxes[0][k]))
        source_int[1]+=dt*fsum(source);source_abs[1]+=dt*fsum(abs(s) for s in source)
        inventory=inventories(cells)
        residual=[inventory[k]-initial_inventory[k]+boundary_int[k]-source_int[k] for k in range(4)]
        normalized=[abs(residual[k])/max(initial_abs[k],boundary_abs[k],source_abs[k],scales[k]) for k in range(4)]
        now=[min(w[0] for w in states),min(w[2] for w in states),min(w[2]/(w[0]*eos.R) for w in states),min(w[3] for w in states),max(w[3] for w in states),max(abs(w[1])/eos.sound_speed(w) for w in states)]
        extrema=[min(a,b) if i<4 else max(a,b) for i,(a,b) in enumerate(zip(extrema,now))]
        history.append(dict(step=step,time=t,dt=dt,max_CFL=dt/dt_unit,cell_limiting_dt=limiting,
                            inventory=inventory,boundary=list(boundary_int),source=list(source_int),residual=residual,normalized=normalized))
        if next_sample is not None and t>=next_sample-4e-16:
            observe_sensor();sample_number+=1;next_sample=sample_number*sample_interval
        if progress and step%200==0:progress(step,t)
    final_inventory=inventories(cells)
    return dict(status=status,reason=reason,time=t,steps=step,wall_seconds=time.monotonic()-started,
                cells=cells,primitive=states,temperature=[w[2]/(w[0]*eos.R) for w in states],
                Mach=[w[1]/eos.sound_speed(w) for w in states],face_fluxes=fluxes,
                initial_inventory=initial_inventory,final_inventory=final_inventory,
                boundary_flux_integral=boundary_int,source_integral=source_int,ledger=history,sensors=signals,
                minimum_dt=minimum_dt,max_CFL=max_cfl,rejected_steps=rejections,
                extrema=dict(zip(('min_rho','min_p','min_T','min_Y','max_Y','max_Mach'),extrema)),
                hllc_flux_count=hllc_count,hlle_fallback_count=sum(fallbacks.values()),fallback_reason=fallbacks,
                fallback_records=fallback_records,fallback_records_truncated=sum(fallbacks.values())>100)
