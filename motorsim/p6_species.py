"""P6 passive four-species transport on the P5-C conservative backbone.

Species are bookkeeping fields only.  They do not alter the EOS or energy.
"""
from dataclasses import dataclass
from math import fsum, isfinite

SPECIES = ("fresh_air", "fuel", "residual", "burned")


def validate_species(values, mass, *, tol=1e-14):
    values = tuple(float(x) for x in values)
    if len(values) != 4 or not isfinite(mass) or mass < 0:
        raise ValueError("invalid species state")
    if any(not isfinite(x) or x < -tol for x in values):
        raise ValueError("inadmissible species mass")
    if abs(fsum(values) - mass) > tol * max(1.0, mass):
        raise ValueError("species masses do not sum to total mass")
    return values


def donor_species(mass_flux, donor, receiver=None):
    """Return conservative species flux using the actual upstream donor."""
    if mass_flux > 0:
        source = donor
    elif mass_flux < 0:
        if receiver is None:
            raise ValueError("reverse flow requires receiver donor state")
        source = receiver
    else:
        return (0.0, 0.0, 0.0, 0.0)
    validate_species(source, fsum(source))
    return tuple(mass_flux * x / fsum(source) for x in source)


@dataclass
class SpeciesChamber:
    mass: float
    species: tuple

    def __post_init__(self):
        self.species = validate_species(self.species, self.mass)

    def apply(self, outward_species_flux, dt):
        if dt <= 0 or len(outward_species_flux) != 4:
            raise ValueError("invalid species update")
        values = tuple(a - dt * b for a, b in zip(self.species, outward_species_flux))
        self.species = validate_species(values, self.mass - dt * sum(outward_species_flux))
        self.mass -= dt * sum(outward_species_flux)


def advect_species(left, right, mass_flux, dt, volume):
    """Apply one shared interface mass flux to adjacent finite volumes."""
    if dt <= 0 or volume <= 0:
        raise ValueError("invalid transport step")
    flux = donor_species(mass_flux, left, right)
    lmass = fsum(left) - dt * mass_flux / volume
    rmass = fsum(right) + dt * mass_flux / volume
    lnew = tuple(a - dt * f / volume for a, f in zip(left, flux))
    rnew = tuple(a + dt * f / volume for a, f in zip(right, flux))
    return validate_species(lnew, lmass), validate_species(rnew, rmass), flux


def atmospheric_species():
    return (1.0, 0.0, 0.0, 0.0)


class P6SpeciesLedger:
    """Independent global species inventory and external exchange ledger."""
    def __init__(self, components):
        self.initial = tuple(fsum(c[i] for c in components) for i in range(4))
        self.current = list(self.initial)
        self.external = [0.0] * 4

    def update(self, components, external_flux=(0.0, 0.0, 0.0, 0.0)):
        self.current = [fsum(c[i] for c in components) for i in range(4)]
        self.external = [a + b for a, b in zip(self.external, external_flux)]

    def report(self):
        delta = tuple(b - a for a, b in zip(self.initial, self.current))
        residual = tuple(d - e for d, e in zip(delta, self.external))
        return {name: {"initial": self.initial[i], "final": self.current[i],
                       "external": self.external[i], "residual": residual[i]}
                for i, name in enumerate(SPECIES)}
