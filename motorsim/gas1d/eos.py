"""Calorically perfect ideal gas. Primitive order: rho, u, p, Y."""
from dataclasses import dataclass
from math import isfinite, sqrt


class InvalidState(ValueError):
    pass


@dataclass(frozen=True)
class IdealGas:
    R: float = 287.0
    gamma: float = 1.35

    def __post_init__(self):
        if not isfinite(self.R) or not isfinite(self.gamma) or self.R<=0 or self.gamma<=1:
            raise InvalidState('Invalid EOS')

    @property
    def cv(self): return self.R/(self.gamma-1)

    @property
    def cp(self): return self.gamma*self.cv

    def validate(self, w):
        r,u,p,y=w
        if not all(isfinite(v) for v in w) or r<=0 or p<=0 or not 0<=y<=1:
            raise InvalidState('rho/p/Y inadmissible')
        temperature=p/(r*self.R)
        if not isfinite(temperature) or temperature<=0: raise InvalidState('T inadmissible')
        return w

    def conservative(self, w):
        r,u,p,y=self.validate(w)
        q=(r,r*u,p/(self.gamma-1)+0.5*r*u*u,r*y)
        if not all(isfinite(v) for v in q): raise InvalidState('Nonfinite conserved state')
        return q

    def primitive(self, q):
        r,m,e,z=q
        if not all(isfinite(v) for v in q) or r<=0 or not 0<=z<=r:
            raise InvalidState('Conserved rho/species inadmissible')
        u=m/r;p=(self.gamma-1)*(e-0.5*m*u)
        return self.validate((r,u,p,z/r))

    def sound_speed(self,w): return sqrt(self.gamma*w[2]/w[0])

    def flux(self,w):
        r,u,p,y=w;m=r*u
        return (m,m*u+p,u*(self.gamma*p/(self.gamma-1)+0.5*r*u*u),m*y)
