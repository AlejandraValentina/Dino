import pytest

from motorsim.p6_species import (SPECIES, P6SpeciesLedger, SpeciesChamber,
                                  advect_species, atmospheric_species,
                                  donor_species, validate_species)


def test_four_species_sum_and_atmosphere():
    assert atmospheric_species() == (1.0, 0.0, 0.0, 0.0)
    assert validate_species((.5, .2, .2, .1), 1.0) == (.5, .2, .2, .1)


def test_forward_and_reverse_use_actual_donor():
    left = (.8, .1, .1, 0.0)
    right = (.1, .2, .3, .4)
    assert donor_species(2.0, left, right) == (1.6, .2, .2, 0.0)
    assert donor_species(-2.0, left, right) == tuple(-2.0*x for x in right)


def test_shared_flux_updates_both_sides():
    left, right, flux = advect_species((.8, .1, .1, 0), (.1, .2, .3, .4), .2, .01, 1.0)
    assert all(x >= 0 for x in left + right)
    assert all(abs(a + b - c - d) < 1e-12 for a,b,c,d in zip(left,right,(.8,.1,.1,0),(.1,.2,.3,.4)))
    assert sum(flux) == pytest.approx(.2)


def test_independent_species_ledger():
    ledger = P6SpeciesLedger([(.8, .1, .1, 0.0), (.1, .2, .3, .4)])
    ledger.update([(.7, .1, .1, .1), (.2, .2, .3, .3)], (.0, .0, .0, .0))
    report = ledger.report()
    assert set(report) == set(SPECIES)
    assert all(abs(v['residual']) < 1e-12 for v in report.values())


def test_chamber_species_admissibility():
    chamber = SpeciesChamber(1.0, (.8, .1, .1, 0.0))
    chamber.apply((.1, 0.0, 0.0, 0.0), .1)
    assert sum(chamber.species) == pytest.approx(chamber.mass)
