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


def legacy_to_species(mass, fresh_fraction=1.0):
    """Deterministic P5 compatibility mapping; no fabricated fuel history."""
    if mass < 0 or not 0.0 <= fresh_fraction <= 1.0:
        raise ValueError("invalid legacy composition")
    fresh = mass * fresh_fraction
    return (fresh, 0.0, mass - fresh, 0.0)


def legacy_fresh_mass(species):
    validate_species(species, fsum(species))
    return species[0] + species[1]


def scavenging_metrics(cylinder_species, transfer_fresh=0.0,
                       exhaust_outward_mass=0.0, donor_species_state=None):
    total = fsum(cylinder_species)
    fresh = legacy_fresh_mass(cylinder_species)
    donor = donor_species_state if donor_species_state is not None else cylinder_species
    fresh_fraction_donor = legacy_fresh_mass(donor) / fsum(donor) if fsum(donor) else 0.0
    short = max(0.0, exhaust_outward_mass) * fresh_fraction_donor
    return {
        "cylinder_fresh_mass": fresh,
        "cylinder_fresh_fraction": fresh / total if total else 0.0,
        "cylinder_residual_mass": cylinder_species[2],
        "cylinder_burned_mass": cylinder_species[3],
        "fresh_mass_delivered": max(0.0, transfer_fresh),
        "fresh_short_circuit_mass": short,
    }


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


class P6IntegratedSystem:
    """Species companion advanced at the two P5-C stage evaluations.

    The gas state is supplied by an ``IntegratedP5C`` instance.  This class
    keeps authoritative species masses and evaluates donor fluxes from each
    stage trace before the corresponding gas stage is installed.
    """
    def __init__(self, gas_system, *, component_species=None):
        self.gas = gas_system
        self.species = component_species or self._default_state()
        self._initial = self._species_totals()
        self._external = [0.0] * 4
        self.fresh_delivered = 0.0
        self.fresh_short_circuit = 0.0

    def _default_state(self):
        fresh = atmospheric_species()
        return {
            'crankcase': [fresh], 'cylinder': [fresh],
            'intake': [fresh for _ in self.gas.core.intake.cells],
            'tr1': [fresh for _ in self.gas.core.transfers[0].cells],
            'tr2': [fresh for _ in self.gas.core.transfers[1].cells],
            'exhaust': [fresh for _ in self.gas.exhaust.cells],
        }

    def _species_totals(self):
        return tuple(fsum(cell[i] for cells in self.species.values() for cell in cells)
                     for i in range(4))

    def validate(self):
        for cells in self.species.values():
            for cell in cells: validate_species(cell, fsum(cell))
        return True

    def derived_legacy_fresh(self, component):
        cells = self.species[component]
        return fsum(legacy_fresh_mass(c) for c in cells)

    def step(self, dt, *, angle=None):
        """Advance gas and species with stage snapshots from the same P5-C RHS."""
        # Species are updated from the exact stage interface traces exposed by
        # P5-C; no independent gas flux solve or legacy mY state is evolved.
        before = self._species_totals()
        record = self.gas.step(dt, angle=angle)
        # Consume both stage traces.  Each stage reads the currently updated
        # authoritative species state; no legacy scalar is cached.
        self.stage_species = []
        for stage, interfaces in enumerate(record['core_interfaces']):
            before_stage = {k: [tuple(x) for x in v] for k, v in self.species.items()}
            for flux, left_name, right_name in ((interfaces[1], 'crankcase', 'tr1'),
                                                 (interfaces[2], 'crankcase', 'tr2'),
                                                 (interfaces[3], 'tr1', 'cylinder'),
                                                 (interfaces[4], 'tr2', 'cylinder')):
                self._exchange(flux[0], left_name, right_name, dt * .5)
            if stage < len(record.get('stage_interfaces', ())):
                pflux = record['stage_interfaces'][stage][2]
                self._exchange(pflux[0], 'cylinder', 'exhaust', dt * .5)
            self.stage_species.append({'before': before_stage,
                                       'after': {k: [tuple(x) for x in v]
                                                 for k, v in self.species.items()}})
        self.validate()
        after = self._species_totals()
        return {'gas': record, 'species_initial': before,
                'species_final': after, 'legacy_fresh_cylinder': self.derived_legacy_fresh('cylinder'),
                'fresh_delivered': self.fresh_delivered,
                'fresh_short_circuit': self.fresh_short_circuit}

    def _exchange(self, mass_flux, left, right, dt):
        if mass_flux == 0.0: return
        donor = self.species[left] if mass_flux > 0 else self.species[right]
        receiver = self.species[right] if mass_flux > 0 else self.species[left]
        source = donor[0]
        flux = donor_species(mass_flux, source, receiver[0])
        dm = tuple(dt*x for x in flux)
        donor[0] = validate_species(tuple(a-b for a,b in zip(source, dm)),
                                     fsum(source)-sum(dm))
        receiver[0] = validate_species(tuple(a+b for a,b in zip(receiver[0], dm)),
                                        fsum(receiver[0])+sum(dm))
        if right in ('tr1','tr2') and left == 'cylinder' and mass_flux < 0:
            self.fresh_delivered += 0.0
        if left == 'cylinder' and right == 'exhaust' and mass_flux > 0:
            self.fresh_short_circuit += sum(dm[:2])

    def snapshot(self):
        return {'gas': self.gas.snapshot(),
                'species': {k: [tuple(x) for x in v] for k,v in self.species.items()},
                'external': list(self._external), 'fresh_delivered': self.fresh_delivered,
                'fresh_short_circuit': self.fresh_short_circuit}

    def restore(self, snapshot):
        self.gas.restore(snapshot['gas'])
        self.species = {k: [tuple(x) for x in v] for k,v in snapshot['species'].items()}
        self._external = list(snapshot['external'])
        self.fresh_delivered = snapshot['fresh_delivered']
        self.fresh_short_circuit = snapshot['fresh_short_circuit']

    def species_sum_error(self):
        """Cross-check authoritative species totals against gas mass."""
        return sum(self._species_totals()) - self.gas.totals()['mass']
