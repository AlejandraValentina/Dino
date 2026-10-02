import math
import unittest

from motorsim.scavenging import (ScavengingInput, calculate_scavenging_metrics,
                                 reference_charge_mass)


class ScavengingMetricTests(unittest.TestCase):
    def setUp(self):
        self.inputs = ScavengingInput(
            reference_mass_kg=0.01,
            fresh_delivered_kg=0.012,
            fresh_short_circuit_kg=0.002,
            species_at_transfer_close_kg=(0.003, 0.001, 0.006, 0.0),
            species_at_exhaust_close_kg=(0.004, 0.001, 0.004, 0.001),
        )

    def test_all_metrics_match_independent_analytic_values(self):
        result = calculate_scavenging_metrics(self.inputs)
        ratios = result["ratios"]
        self.assertEqual(result["schema"], "MOTORSIM_2T_SCAVENGING_METRICS_V1")
        self.assertAlmostEqual(ratios["delivery_ratio"]["value"], 1.2)
        self.assertAlmostEqual(ratios["trapping_efficiency"]["value"], 5.0 / 12.0)
        self.assertAlmostEqual(ratios["scavenging_efficiency"]["value"], 0.5)
        self.assertAlmostEqual(ratios["charging_efficiency"]["value"], 0.5)
        self.assertAlmostEqual(ratios["trapping_ratio"]["value"], 2.4)
        self.assertAlmostEqual(ratios["residual_fraction"]["value"], 0.4)
        self.assertAlmostEqual(ratios["purity_at_transfer_close"]["value"], 0.4)
        self.assertAlmostEqual(ratios["purity_at_exhaust_close"]["value"], 0.5)
        self.assertAlmostEqual(ratios["short_circuit_fraction"]["value"], 1.0 / 6.0)
        self.assertEqual(result["masses_kg"]["fresh_retained"], 0.005)
        self.assertEqual(result["masses_kg"]["fresh_lost"], 0.002)

    def test_reference_mass_uses_single_cylinder_swept_volume(self):
        mass = reference_charge_mass(52.0, 46.0, 101325.0, 300.0, 287.0)
        volume_m3 = math.pi * (0.052 ** 2) * 0.046 / 4.0
        expected = (101325.0 / (287.0 * 300.0)) * volume_m3
        self.assertAlmostEqual(mass, expected, places=15)

    def test_zero_denominators_are_explicitly_undefined(self):
        zero = ScavengingInput(0.0, 0.0, 0.0, (0.0,) * 4, (0.0,) * 4)
        result = calculate_scavenging_metrics(zero)
        ratios = result["ratios"]
        for name in ("delivery_ratio", "trapping_efficiency", "scavenging_efficiency",
                     "charging_efficiency", "trapping_ratio", "residual_fraction",
                     "purity_at_transfer_close", "purity_at_exhaust_close",
                     "short_circuit_fraction"):
            with self.subTest(name=name):
                self.assertIsNone(ratios[name]["value"])
                self.assertEqual(ratios[name]["status"], "UNDEFINED")
                self.assertEqual(ratios[name]["reason"], "ZERO_DENOMINATOR")

    def test_each_denominator_is_independent(self):
        # Delivery=0 but retained state exists; transfer purity is still valid.
        source = ScavengingInput(0.01, 0.0, 0.0, (0.2, 0.0, 0.8, 0.0),
                                 (0.1, 0.0, 0.9, 0.0))
        ratios = calculate_scavenging_metrics(source)["ratios"]
        self.assertEqual(ratios["trapping_efficiency"]["status"], "UNDEFINED")
        self.assertEqual(ratios["short_circuit_fraction"]["status"], "UNDEFINED")
        self.assertAlmostEqual(ratios["purity_at_transfer_close"]["value"], 0.2)
        self.assertAlmostEqual(ratios["purity_at_exhaust_close"]["value"], 0.1)

    def test_invalid_masses_and_boolean_numerics_are_rejected(self):
        for value in (-1.0, math.nan, math.inf, True, "0.1"):
            with self.subTest(value=value):
                bad = ScavengingInput(value, 0.012, 0.002,
                                      (0.003, 0.001, 0.006, 0.0),
                                      (0.004, 0.001, 0.004, 0.001))
                with self.assertRaises(ValueError):
                    calculate_scavenging_metrics(bad)
        bad_species = ScavengingInput(0.01, 0.012, 0.002,
                                      (0.003, -0.001, 0.006, 0.0),
                                      (0.004, 0.001, 0.004, 0.001))
        with self.assertRaises(ValueError):
            calculate_scavenging_metrics(bad_species)


if __name__ == "__main__":
    unittest.main()
