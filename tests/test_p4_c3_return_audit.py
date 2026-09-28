import unittest

from dev_orchestrator.p4_c3_return_audit import (
    _momentum_audit, classify, _physical_flux,
)


class P4C3ReturnAuditTests(unittest.TestCase):
    def test_momentum_audit_rejects_productive_terms(self):
        stage = {
            "dt": 0.1,
            "primitive": [[1.0, 0.0, 100000.0, 0.2]],
            "conservative": [[1.0, 0.0, 250000.0, 0.2]],
            "chamber_state": [0.1, 25000.0, 0.02],
        }
        info = {"audit_stages": {"stage_a": stage, "stage_b": stage,
                                 "after": stage}}
        geometry = {"areas": [1.0, 1.0]}
        # Poisoned names must not be read by the independent auditor.
        info["momentum_face_fluxes"] = {"left": 1e99, "right": -1e99}
        info["momentum_source_sum"] = 1e99
        audited = _momentum_audit([(0.1, info)], geometry)
        self.assertEqual(audited["product_field_names_used"], [])
        self.assertNotEqual(audited["rows"][0]["recomputed_stage_a"]["left"], 1e99)

    def test_no_unapproved_equality_threshold_can_pass_c3(self):
        self.assertEqual(classify(True, True, True,
                                  {"status": "INCONCLUSIVE"},
                                  {"status": "INCONCLUSIVE"}),
                         "P4_SCI_C3_INCONCLUSIVE")

    def test_physical_flux_has_conservative_energy_and_species(self):
        flux = _physical_flux((2.0, 3.0, 5.0, 0.25))
        self.assertEqual(flux[0], 6.0)
        self.assertEqual(flux[3], 1.5)


if __name__ == "__main__":
    unittest.main()
