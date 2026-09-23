"""Minimal integrated intake/transfer fixture for conditional P5-B.

Composes P5-A interfaces; exhaust and periodic engine operation are absent.
"""
from dataclasses import dataclass
from copy import deepcopy
from .duct_network import interface_exchange
from .coupling import ChamberState
from .gas1d.eos import IdealGas


@dataclass
class Chamber:
    primitive: tuple
    volume: float

    def inventory(self, eos):
        rho,u,p,y = eos.validate(self.primitive)
        mass = rho*self.volume
        return (mass, mass*y, p*self.volume/(eos.gamma-1))

    def thermodynamics(self, eos):
        rho,u,p,y = eos.validate(self.primitive)
        return rho, p, p/(rho*eos.R), y


class IntegratedIntakeTransfer:
    """Atmosphere→intake→crankcase with two independent transfer endpoints."""
    def __init__(self, crankcase, cylinder, duct_states, *, eos=None):
        if len(duct_states) != 3:
            raise ValueError("expected intake, transfer1 and transfer2 states")
        self.eos = eos or IdealGas()
        self.crankcase = crankcase
        self.cylinder = cylinder
        self.duct_states = list(duct_states)
        self.angle = 0.0
        self.history = []

    def _areas(self, angle):
        # Contractual 2T timing fixture: intake opens 270..360 and transfers
        # 100..220 degrees. Values are intentionally explicit and deterministic.
        a = angle % 360.0
        intake = 1e-4 if 270.0 <= a < 360.0 else 0.0
        transfer = 1e-4 if 100.0 <= a < 220.0 else 0.0
        return intake, transfer, transfer

    def step(self, dt, angle=None):
        if dt <= 0: raise ValueError("dt must be positive")
        self.angle = self.angle + 360.0*dt if angle is None else float(angle)
        ai, at1, at2 = self._areas(self.angle)
        atmosphere = (101325.0/(self.eos.R*300.0), 0.0, 101325.0, .0)
        fluxes = [interface_exchange(self.crankcase, atmosphere, ai, -1, eos=self.eos)]
        for area in (at1, at2):
            fluxes.append(interface_exchange(self.crankcase, self.duct_states[1], area, 1, eos=self.eos))
        self.history.append({'angle':self.angle,'areas':(ai,at1,at2),
                             'fluxes':[f['outward'] for f in fluxes]})
        return self.history[-1]

    def snapshot(self):
        return {'angle':self.angle,'crankcase':deepcopy(self.crankcase),
                'cylinder':deepcopy(self.cylinder),'duct_states':deepcopy(self.duct_states)}

    def restore(self, snap):
        self.angle=snap['angle']; self.crankcase=deepcopy(snap['crankcase'])
        self.cylinder=deepcopy(snap['cylinder']); self.duct_states=deepcopy(snap['duct_states'])
