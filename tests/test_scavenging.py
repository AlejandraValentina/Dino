import math
import unittest

from motorsim.scavenging import (ScavengingInput, calculate_scavenging_metrics,
                                 reference_charge_mass,
                                 scavenging_metrics_from_cycle)


class ScavengingMetricTests(unittest.TestCase):
    def setUp(self):
        self.inputs = ScavengingInput(
            reference_mass_kg=0.01,
            fresh_delivered_kg=0.012,
            fresh_short_circuit_kg=0.002,
            species_at_transfer_close_kg=(0.003, 0.001, 0.006, 0.0),
            species_at_exhaust_close_kg=(0.004, 0.001, 0.004, 0.001),
        )

    @staticmethod
    def primary_cycle():
        terminal_gas = [1.0, 2.0, 3.0]
        terminal_species = {"cylinder": [[0.004, 0.001, 0.004, 0.001]]}
        rows = [
            {"angle_deg": 40.0, "state": [0.0],
             "species_mass": {"cylinder": [[0.0, 0.0, 0.0, 0.0]]},
             "fresh_delivery_cumulative_kg": 0.0,
             "fresh_short_circuit_cumulative_kg": 0.0},
            {"angle_deg": 100.0, "state": [1.0],
             "species_mass": {"cylinder": [[0.003, 0.001, 0.006, 0.0]]},
             "fresh_delivery_cumulative_kg": 0.004,
             "fresh_short_circuit_cumulative_kg": 0.0002},
            {"angle_deg": 250.0, "state": terminal_gas,
             "species_mass": terminal_species,
             "fresh_delivery_cumulative_kg": 0.012,
             "fresh_short_circuit_cumulative_kg": 0.002},
        ]
        return {
            "schema": "REFERENCE_ENGINE_HYBRID_CYCLE_PRIMARY_V1",
            "terminal_state": {"gas_conservative": terminal_gas,
                               "species_mass": terminal_species},
            "trajectory_terminal_state": terminal_gas,
            "trajectory_last_state": terminal_gas,
            "trajectory_last_species_mass": terminal_species,
            "trajectory": rows,
            "cycle_start_cumulative": {"fresh_delivery": 0.0,
                                       "fresh_short_circuit": 0.0},
            "observables": {"fresh_delivery_kg": 0.012,
                            "fresh_short_circuit_kg": 0.002},
        }

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

    def test_cycle_metrics_bind_to_exact_primary_event_snapshots_and_ledgers(self):
        result = scavenging_metrics_from_cycle(
            self.primary_cycle(), reference_mass_kg=0.01,
            transfer_close_angle_deg=100.0, exhaust_close_angle_deg=250.0)
        self.assertAlmostEqual(result["ratios"]["purity_at_transfer_close"]["value"], 0.4)
        self.assertAlmostEqual(result["ratios"]["purity_at_exhaust_close"]["value"], 0.5)
        self.assertAlmostEqual(result["masses_kg"]["fresh_lost"], 0.002)

    def test_cycle_metrics_reject_missing_events_and_stale_summaries(self):
        cycle = self.primary_cycle()
        with self.assertRaisesRegex(ValueError, "Falta snapshot"):
            scavenging_metrics_from_cycle(cycle, reference_mass_kg=0.01,
                                          transfer_close_angle_deg=101.0,
                                          exhaust_close_angle_deg=250.0)
        cycle = self.primary_cycle()
        cycle["observables"]["fresh_delivery_kg"] = 99.0
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            scavenging_metrics_from_cycle(cycle, reference_mass_kg=0.01,
                                          transfer_close_angle_deg=100.0,
                                          exhaust_close_angle_deg=250.0)
        cycle = self.primary_cycle()
        cycle["observables"]["fresh_delivery_kg"] = True
        with self.assertRaisesRegex(ValueError, "número"):
            scavenging_metrics_from_cycle(cycle, reference_mass_kg=0.01,
                                          transfer_close_angle_deg=100.0,
                                          exhaust_close_angle_deg=250.0)

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
