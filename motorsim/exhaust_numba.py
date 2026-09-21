"""Serial float64 HLLC adaptation; numerical reference retained independently."""
import numpy as np
from math import sqrt,isfinite
from numba import njit
from .gas1d.eos import InvalidState
from .gas1d.riemann import hllc_flux as reference_hllc

@njit(cache=True, fastmath=False, parallel=False)
def validate(w,R):
    r,u,p,y=w
    if not (np.isfinite(w).all() and r>0 and p>0 and 0<=y<=1):
        raise ValueError('rho/p/Y inadmissible')
    T=p/(r*R)
    if not isfinite(T) or T<=0:raise ValueError('Temperature inadmissible')

@njit(cache=True, fastmath=False, parallel=False)
def flux(w,gamma):
    r,u,p,y=w;m=r*u
    return np.array([m,m*u+p,u*(gamma*p/(gamma-1)+.5*r*u*u),m*y])

@njit(cache=True, fastmath=False, parallel=False)
def conservative(w,gamma):
    r,u,p,y=w
    return np.array([r,r*u,p/(gamma-1)+.5*r*u*u,r*y])

@njit(cache=True, fastmath=False, parallel=False)
def estimate_wave_speeds(left,right,gamma,R):
    rl,ul,pl,_=left;rr,ur,pr,_=right
    al=sqrt(gamma*left[2]/left[0]);ar=sqrt(gamma*right[2]/right[0])
    wl=sqrt(rl);wr=sqrt(rr);g=gamma
    hl=g*pl/((g-1)*rl)+ul*ul/2;hr=g*pr/((g-1)*rr)+ur*ur/2
    u=(wl*ul+wr*ur)/(wl+wr);h=(wl*hl+wr*hr)/(wl+wr)
    a2=(g-1)*(h-u*u/2)
    if not isfinite(a2) or a2<=0: raise ValueError('Invalid Roe speed')
    a=sqrt(a2)
    sl=min(ul-al,ur-ar,u-a);sr=max(ul+al,ur+ar,u+a)
    if not isfinite(sl) or not isfinite(sr) or sl>=sr: raise ValueError('Invalid wave bounds')
    return sl,sr


@njit(cache=True, fastmath=False, parallel=False)
def hlle_flux(left,right,gamma,R,speeds):
    sl,sr=speeds
    fl=flux(left,gamma);fr=flux(right,gamma)
    if sl>=0:return fl
    if sr<=0:return fr
    ql=conservative(left,gamma);qr=conservative(right,gamma)
    return np.array([(sr*fl[k]-sl*fr[k]+sl*sr*(qr[k]-ql[k]))/(sr-sl) for k in range(4)])


@njit(cache=True, fastmath=False, parallel=False)
def hllc_flux(left,right,gamma,R):
    """Return (flux, (SL,SM,SR), fallback_reason). No in-place state changes."""
    validate(left,R);validate(right,R)
    sl,sr=estimate_wave_speeds(left,right,gamma,R)
    rl,ul,pl,yl=left;rr,ur,pr,yr=right
    if np.all(left==right):return flux(left,gamma),(sl,ul,sr),0
    fl=flux(left,gamma);fr=flux(right,gamma)
    if sl>=0:return fl,(sl,ul,sr),0
    if sr<=0:return fr,(sl,ur,sr),0
    denominator=rl*(sl-ul)-rr*(sr-ur)
    reason=0;sm=0
    if denominator==0 or not isfinite(denominator):reason=1
    else:
        sm=(pr-pl+rl*ul*(sl-ul)-rr*ur*(sr-ur))/denominator
        if not isfinite(sm) or not sl<sm<sr:reason=2
    stars=[]
    if reason == 0:
        for w,s in ((left,sl),(right,sr)):
            r,u,p,y=w
            if s==sm or s==u:reason=3;break
            rs=r*(s-u)/(s-sm);ps=p+r*(s-u)*(sm-u)
            es=p/((gamma-1)*r)+u*u/2+(sm-u)*(sm+p/(r*(s-u)))
            if not (isfinite(rs) and isfinite(ps) and isfinite(es)) or rs<=0 or ps<=0 or es-sm*sm/2<=0:
                reason=4;break
            stars.append((rs,rs*sm,rs*es,rs*y))
    if reason:
        return hlle_flux(left,right,gamma,R,(sl,sr)),(sl,sm,sr),reason
    w,s,star,f=(left,sl,stars[0],fl) if sm>=0 else (right,sr,stars[1],fr)
    q=conservative(w,gamma)
    out=np.array([f[k]+s*(star[k]-q[k]) for k in range(4)])
    # F_mass*=rho*u+S*(rho*-rho)=rho*SM by Rankine-Hugoniot.
    # The product preserves SM's sign without subtracting nearly equal states.
    # Species shares this same mass flux and the same HLLC contact-wave donor.
    mass=star[0]*sm
    return np.array([mass,out[1],out[2],mass*w[3]]),(sl,sm,sr),0

@njit(cache=True, fastmath=False, parallel=False)
def faces(left,right,gamma,R):
    n=len(left);out=np.empty((n,4));speeds=np.empty((n,3));codes=np.zeros(n,np.int64)
    for i in range(n):
        f,s,c=hllc_flux(left[i],right[i],gamma,R)
        out[i]=f;speeds[i]=s;codes[i]=c
    return out,speeds,codes

def hllc(left,right,eos):
    try:out,speeds,codes=faces(left,right,eos.gamma,eos.R)
    except ValueError as exc:raise InvalidState(str(exc)) from exc
    reasons={};fallback={}
    # Preserve reference exceptional semantics, including undefined SM.
    for i in np.flatnonzero(codes):
        f,s,r=reference_hllc(tuple(left[i]),tuple(right[i]),eos)
        out[i]=f;speeds[i]=(s[0],np.nan if s[1] is None else s[1],s[2])
        if r:reasons[int(i)]=r;fallback[int(i)]=s
    return out,speeds,reasons,fallback


@njit(cache=True, fastmath=False, parallel=False)
def primitive_numeric(cells,volumes,gamma,R):
    w=np.empty_like(cells)
    for i in range(len(cells)):
        r,m,e,z=cells[i]/volumes[i]
        if not (isfinite(r) and isfinite(m) and isfinite(e) and isfinite(z) and r>0 and 0<=z<=r):
            raise ValueError('Conserved rho/species inadmissible')
        u=m/r;p=(gamma-1)*(e-.5*m*u)
        w[i]=r,u,p,z/r
        validate(w[i],R)
    return w

def primitive(cells,volumes,eos):
    try:return primitive_numeric(cells,volumes,eos.gamma,eos.R)
    except ValueError as exc:raise InvalidState(str(exc)) from exc

@njit(cache=True, fastmath=False, parallel=False)
def admissible(w,R):
    r,u,p,y=w
    if not (np.isfinite(w).all() and r>0 and p>0 and 0<=y<=1):return False
    T=p/(r*R)
    return isfinite(T) and T>0

@njit(cache=True, fastmath=False, parallel=False)
def reconstruct_numeric(w,lo,hi,dl,dr,left_offset,right_offset,R):
    n=len(w);lf=np.empty_like(w);rf=np.empty_like(w);bad=np.zeros(n,np.bool_)
    for i in range(n):
        for k in range(4):
            l=lo[k] if i==0 else w[i-1,k];r=hi[k] if i==n-1 else w[i+1,k]
            a=(w[i,k]-l)/dl[i,0];b=(r-w[i,k])/dr[i,0]
            slope=0. if a==0 or b==0 or (a>0)!=(b>0) else (a if abs(a)<=abs(b) else b)
            lf[i,k]=w[i,k]+slope*left_offset[i,0];rf[i,k]=w[i,k]+slope*right_offset[i,0]
        if not (admissible(lf[i],R) and admissible(rf[i],R)):
            lf[i]=w[i];rf[i]=w[i];bad[i]=True
    return lf,rf,bad

from .exhaust_batch import Kernel as ReferenceKernel
class Kernel(ReferenceKernel):
    def reconstruct(self,w,boundaries):
        lo=boundaries[0].face_state(tuple(w[0].tolist()),-1,self.eos)
        hi=boundaries[1].face_state(tuple(w[-1].tolist()),1,self.eos)
        a,b,bad=reconstruct_numeric(w,np.array(lo),np.array(hi),self.dl,self.dr,self.left_offset,self.right_offset,self.eos.R)
        return a,b,np.flatnonzero(bad).tolist()

def solve_exhaust(*args,**kwargs):
    from .exhaust_numpy import solve_exhaust as reference
    import sys
    return reference(*args,numeric_backend=sys.modules[__name__],**kwargs)
