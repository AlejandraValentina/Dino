"""Isolated P3 interface preflight. No production connection or time integrator.

The verified reservoir closure is reused unchanged. Its backflow limitations
propagate as errors; this module neither switches closure nor clips states.
"""
from dataclasses import dataclass
from math import isfinite

from .gas1d.boundary import Boundary
from .gas1d.eos import IdealGas, InvalidState


@dataclass(frozen=True)
class ChamberState:
    mass: float
    internal_energy: float
    fresh_mass: float
    volume: float

    def thermodynamics(self, eos: IdealGas):
        if not all(isfinite(x) for x in (self.mass, self.internal_energy, self.fresh_mass, self.volume)):
            raise InvalidState('Nonfinite chamber state')
        if min(self.mass, self.internal_energy, self.volume) <= 0 or not 0 <= self.fresh_mass <= self.mass:
            raise InvalidState('Inadmissible chamber state')
        rho = self.mass / self.volume
        pressure = (eos.gamma - 1) * self.internal_energy / self.volume
        temperature = self.internal_energy / (self.mass * eos.cv)
        fraction = self.fresh_mass / self.mass
        eos.validate((rho, 0., pressure, fraction))
        return rho, pressure, temperature, fraction


@dataclass(frozen=True)
class SharedFlux:
    face_state: tuple
    outward: tuple  # mass, axial momentum, total energy, fresh mass; outside pipe
    donor: str

    def increments(self, dt):
        """One flux integral, opposite signs. Not a time integration scheme."""
        if not isfinite(dt) or dt < 0:
            raise ValueError('Invalid dt')
        transfer = tuple(dt * self.outward[k] for k in (0, 2, 3))
        return dict(chamber=transfer, pipe=tuple(-x for x in transfer),
                    outward_axial_impulse=dt*self.outward[1])


def interface_flux(chamber, interior, area, normal, *, eos=None):
    eos = eos or IdealGas()
    if normal not in (-1, 1) or not isfinite(area) or area <= 0:
        raise ValueError('Invalid interface area/normal')
    _, pressure, temperature, fraction = chamber.thermodynamics(eos)
    boundary = Boundary('reservoir', p0=pressure, T0=temperature, Y0=fraction)
    face = boundary.face_state(interior, normal, eos)
    # No second Riemann problem or second boundary condition at this face.
    outward = tuple(normal * area * f for f in eos.flux(face))
    donor = 'pipe' if outward[0] > 0 else ('chamber' if outward[0] < 0 else 'none')
    return SharedFlux(face, outward, donor)
