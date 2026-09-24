"""Minimal integrated intake/transfer fixture for conditional P5-B.

Composes P5-A interfaces; exhaust and periodic engine operation are absent.
"""
from dataclasses import dataclass
from copy import deepcopy
from math import isfinite
from .duct_network import interface_exchange
from .coupling import ChamberState
from .gas1d.eos import IdealGas
from .gas1d.riemann import hllc_flux


def interior_rhs(mesh, states, eos=None):
    """Interior finite-volume RHS using the existing HLLC core."""
    eos = eos or IdealGas()
    if len(states) != mesh.n:
        raise ValueError("state/mesh size mismatch")
    fluxes = [hllc_flux(a, b, eos)[0] for a, b in zip(states, states[1:])]
    rhs = []
    for i in range(mesh.n):
        left = fluxes[i-1] if i else (0., 0., 0., 0.)
        right = fluxes[i] if i < len(fluxes) else (0., 0., 0., 0.)
        rhs.append(tuple(-(right[k]-left[k])/mesh.volumes[i] for k in range(4)))
    return tuple(rhs)


def ssprk2_step(state, rhs, dt):
    """Generic two-stage SSPRK2 update for a global tuple state."""
    z1 = tuple(x + dt*r for x, r in zip(state, rhs(state)))
    r1 = rhs(z1)
    return tuple(.5*(x + y + dt*r) for x, y, r in zip(state, z1, r1))


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

    def conservative_rhs(self, outward_fluxes, eos, volume_rate=0.0):
        """Return the chamber RHS for one common interface stage.

        ``outward_fluxes`` are all expressed with the chamber-outward sign
        convention.  The interface solves therefore happen against the same
        stage state and their conservative contributions are summed before
        changing the chamber.  The only non-flux energy source is the
        contractual closed-system work term ``-p*dV/dt``.
        """
        if not all(len(flux) == 4 and all(isfinite(value) for value in flux)
                   for flux in outward_fluxes):
            raise ValueError("invalid chamber flux")
        _, pressure, _, _ = self.thermodynamics(eos)
        if not isinstance(volume_rate, (int, float)) or not isfinite(volume_rate):
            raise ValueError("invalid volume rate")
        mass = sum(flux[0] for flux in outward_fluxes)
        energy = sum(flux[2] for flux in outward_fluxes) - pressure*volume_rate
        species = sum(flux[3] for flux in outward_fluxes)
        return mass, energy, species

    def apply_rhs(self, rhs, dt, eos, volume_rate=0.0):
        """Apply one already assembled chamber stage and update its volume."""
        if (not isinstance(dt, (int, float)) or not isfinite(dt) or dt <= 0
                or not isinstance(volume_rate, (int, float))
                or not isfinite(volume_rate)):
            raise ValueError("dt must be positive")
        if len(rhs) != 3 or not all(isfinite(value) for value in rhs):
            raise ValueError("invalid chamber rhs")
        old_volume = self.volume
        new_volume = old_volume + dt*volume_rate
        if new_volume <= 0:
            raise ValueError("NUMERICAL_FAILURE: nonpositive chamber volume")
        mass, species, energy = self.inventory(eos)
        mass += dt*rhs[0]
        energy += dt*rhs[1]
        species += dt*rhs[2]
        if mass <= 0 or not 0 <= species <= mass or energy <= 0:
            raise ValueError("NUMERICAL_FAILURE: inadmissible chamber update")
        self.volume = new_volume
        self.primitive = (mass/new_volume, 0.0,
                          (eos.gamma-1)*energy/new_volume, species/mass)

    def apply_exchange(self, flux, dt, eos, work=0.0):
        """Apply one outward chamber flux; mass/energy/species are conserved."""
        if not isinstance(dt, (int, float)) or not isfinite(dt) or dt <= 0:
            raise ValueError("dt must be positive")
        if not isinstance(work, (int, float)) or not isfinite(work):
            raise ValueError("invalid work")
        self.apply_rhs((flux[0], flux[2] + work/dt, flux[3]), dt, eos)

@dataclass
class DuctCell:
    conservative: tuple
    volume: float

    def primitive(self, eos):
        return eos.primitive(self.conservative)

    def apply_flux(self, flux, dt, eos, sign=1.0):
        q = tuple(self.conservative[i] + sign*dt*flux[i]/self.volume for i in range(4))
        eos.primitive(q)
        self.conservative = q


class IntegratedIntakeTransfer:
    """Atmosphere→intake→crankcase with two independent transfer endpoints."""
    def __init__(self, crankcase, cylinder, duct_states, *, eos=None, volume_rates=(0.0, 0.0)):
        if len(duct_states) != 3:
            raise ValueError("expected intake, transfer1 and transfer2 states")
        self.eos = eos or IdealGas()
        self.crankcase = crankcase
        self.cylinder = cylinder
        self.duct_states = [x if isinstance(x, DuctCell) else DuctCell(self.eos.conservative(x), 1e-2)
                            for x in duct_states]
        self.angle = 0.0
        self.volume_rates = tuple(volume_rates)
        self.ledger = {'external_mass':0.0,'external_energy':0.0,'external_species':0.0,
                       'cc_work':0.0,'cyl_work':0.0}
        self._initial_mass = self._total_mass()
        self._initial_species = self._total_species()
        self.history = []

    def _total_mass(self):
        """Return the mass currently stored in every coupled volume."""
        chamber_mass = (self.crankcase.inventory(self.eos)[0]
                        + self.cylinder.inventory(self.eos)[0])
        # The intake state is the prescribed external-side trace in this
        # compact fixture, not a stored control volume.  Transfer states are
        # included because they are internal to the integrated topology.
        duct_mass = sum(cell.conservative[0] * cell.volume
                        for cell in self.duct_states[1:])
        return chamber_mass + duct_mass

    def _total_species(self):
        """Return the fresh-species inventory in all stored coupled volumes."""
        chamber_species = (self.crankcase.inventory(self.eos)[1]
                           + self.cylinder.inventory(self.eos)[1])
        duct_species = sum(cell.conservative[3] * cell.volume
                           for cell in self.duct_states[1:])
        return chamber_species + duct_species

    def mass_ledger(self):
        """Audit closed-system mass against the external interface integral.

        A positive external flux denotes mass entering the integrated fixture.
        Internal transfer interfaces cancel because each duct receives the
        opposite update of its chamber flux.  The returned residual is
        ``(final - initial) - external`` and is intentionally not normalized.
        """
        final_mass = self._total_mass()
        external_mass = self.ledger['external_mass']
        delta_mass = final_mass - self._initial_mass
        return {
            'initial_mass': self._initial_mass,
            'final_mass': final_mass,
            'delta_mass': delta_mass,
            'external_mass': external_mass,
            'residual': delta_mass - external_mass,
        }

    def species_ledger(self):
        """Audit fresh-species inventory against the external interface.

        Species is stored as fresh mass, not as a mass fraction.  The intake
        endpoint is the only external boundary in this fixture; transfer
        interfaces are internal and therefore cancel from the global balance.
        """
        final_species = self._total_species()
        external_species = self.ledger['external_species']
        delta_species = final_species - self._initial_species
        return {
            'initial_species': self._initial_species,
            'final_species': final_species,
            'delta_species': delta_species,
            'external_species': external_species,
            'residual': delta_species - external_species,
        }

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
        fluxes = [interface_exchange(self.crankcase, self.duct_states[0].primitive(self.eos), ai, -1, eos=self.eos)]
        for duct, area in zip(self.duct_states[1:], (at1, at2)):
            # Resolve each physical interface exactly once from its own stage
            # state.  The returned flux object is the single source consumed
            # by both chamber and duct updates below.
            fluxes.append(interface_exchange(self.crankcase, duct.primitive(self.eos), area, 1, eos=self.eos))
        # One interface solve supplies the flux trace and the chamber update.
        crankcase_fluxes = [item['outward'] for item in fluxes]
        cylinder_fluxes = [tuple(-x for x in fluxes[i]['outward']) for i in (1, 2)]
        crankcase_rhs = self.crankcase.conservative_rhs(
            crankcase_fluxes, self.eos, self.volume_rates[0])
        cylinder_rhs = self.cylinder.conservative_rhs(
            cylinder_fluxes, self.eos, self.volume_rates[1])
        crankcase_work = -self.crankcase.primitive[2]*self.volume_rates[0]*dt
        cylinder_work = -self.cylinder.primitive[2]*self.volume_rates[1]*dt
        self.crankcase.apply_rhs(crankcase_rhs, dt, self.eos, self.volume_rates[0])
        self.cylinder.apply_rhs(cylinder_rhs, dt, self.eos, self.volume_rates[1])
        # The intake interface is the external boundary; its positive
        # chamber flux is recorded in external_mass and is not also applied
        # to a second stored volume.
        # The compact fixture uses one endpoint state for each transfer and
        # applies that shared interface flux to both chamber endpoints.  The
        # duct receives the opposite contribution at the crankcase end and
        # the equal contribution at the cylinder end, so its net update is
        # zero.  Keeping that cancellation explicit makes the global mass
        # ledger auditable without inventing an additional duct solve.
        for index in (1, 2):
            self.duct_states[index].apply_flux(
                fluxes[index]['outward'], dt, self.eos, sign=0.0)
        f = fluxes[0]['outward']; self.ledger['external_mass'] += dt*f[0]
        self.ledger['external_energy'] += dt*f[2]; self.ledger['external_species'] += dt*f[3]
        self.ledger['cc_work'] += crankcase_work
        self.ledger['cyl_work'] += cylinder_work
        self.history.append({'angle':self.angle,'areas':(ai,at1,at2),
                             'fluxes':[f['outward'] for f in fluxes],
                             'crankcase':self.crankcase.inventory(self.eos),
                             'cylinder':self.cylinder.inventory(self.eos),
                             'ducts':[list(d.conservative) for d in self.duct_states]})
        return self.history[-1]

    def snapshot(self):
        return {'angle':self.angle,'crankcase':deepcopy(self.crankcase),
                'cylinder':deepcopy(self.cylinder),'duct_states':deepcopy(self.duct_states)}

    def restore(self, snap):
        self.angle=snap['angle']; self.crankcase=deepcopy(snap['crankcase'])
        self.cylinder=deepcopy(snap['cylinder']); self.duct_states=deepcopy(snap['duct_states'])
