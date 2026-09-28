import unittest

from dev_orchestrator.p4_c3_return_audit import (
    _momentum_audit, _recompute_stage, _riemann_audit, classify, _physical_flux,
)
from dev_orchestrator.p4_sci_04b import C2_AREA, EOS
from dev_orchestrator.reference.exact_riemann import ExactRiemann


class P4C3ReturnAuditTests(unittest.TestCase):
    def test_riemann_audit_aligns_observed_flux_with_stage_a(self):
        stage_a = {
            "chamber_state": [0.1, 25000.0, 0.02],
            "primitive": [[1.0, 0.0, 100000.0, 0.2]],
        }
        stage_b = {
            "chamber_state": [0.2, 30000.0, 0.04],
            "primitive": [[1.2, 10.0, 120000.0, 0.3]],
        }
        left = (0.1 / 0.0001, 0.0, (EOS.gamma - 1.0) * 25000.0 / 0.0001, 0.02 / 0.1)
        sampled = ExactRiemann(left, tuple(stage_a["primitive"][0]), EOS).sample(0.0)
        observed = [C2_AREA * value for value in _physical_flux(sampled)]
        audit = _riemann_audit({
            "audit_stages": {"stage_a": stage_a, "stage_b": stage_b},
            "interface_flux_observed": observed,
            "interface_normal": -1.0,
            "interface_area": C2_AREA,
        })
        self.assertEqual(audit["left_state"], list(left))
        self.assertEqual(audit["right_state"], stage_a["primitive"][0])
        self.assertAlmostEqual(audit["relative_error"]["max"], 0.0)

    def test_recompute_stage_uses_exact_reflective_wall_for_moving_state(self):
        last = (1.2, 37.0, 125000.0, 0.25)
        stage = {
            "dt": 0.1,
            "primitive": [list(last)],
            "conservative": [[1.2, 1.2 * 37.0, 300000.0, 0.3]],
            "chamber_state": [0.1, 25000.0, 0.02],
        }
        audited = _recompute_stage(stage, {"areas": [1.0, 2.0]})
        ghost = (last[0], -last[1], last[2], last[3])
        reference = ExactRiemann(last, ghost, EOS)
        expected = 2.0 * _physical_flux(reference.sample(0.0))[1]
        self.assertAlmostEqual(audited["right"], expected, places=12)
        self.assertNotAlmostEqual(audited["right"], 2.0 * last[2], places=6)

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
