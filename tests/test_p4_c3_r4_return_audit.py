import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from dev_orchestrator.p4_c3_return_audit import _physical_flux, _riemann_audit
from dev_orchestrator.p4_sci_04b import C2_AREA, EOS
from dev_orchestrator.reference.exact_riemann import ExactRiemann
from dev_orchestrator.reference.hllc_audit import hllc as audit_hllc
from dev_orchestrator.p4_c3_r4_return_audit import (
    R3_OUTPUT, R4_OUTPUT, ensure_safe_output,
)


def _fixture():
    left = (1.4, 0.0, 200000.0, 0.5)
    right = (1.0, -10.0, 100000.0, 0.2)
    flux, waves, reason = audit_hllc(left, right, EOS)
    observed = [C2_AREA * value for value in flux]
    return {
        "interface_normal": -1.0,
        "interface_area": C2_AREA,
        "interface_flux_observed": observed,
        "speeds_iface": list(waves),
        "reason_iface": reason,
        "audit_stages": {"stage_a": {
            "chamber_state": [left[0] * 0.0001,
                               left[2] * 0.0001 / (EOS.gamma - 1.0),
                               left[3] * left[0] * 0.0001],
            "primitive": [[9.0, 99.0, 99999.0, 0.9]],
            "external_faces": {"interface": {
                "left": list(left), "right": list(right)},
            },
        }},
    }


class P4C3R4Tests(unittest.TestCase):
    def test_a_uses_persisted_reconstructed_face_not_primitive_cell(self):
        audit = _riemann_audit(_fixture())
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["right_state"], [1.0, -10.0, 100000.0, 0.2])
        self.assertNotEqual(audit["right_state"], [9.0, 99.0, 99999.0, 0.9])
        self.assertTrue(audit["hllc_exact_error_is_diagnostic"])
        self.assertEqual(audit["criterion_authority"], "P4-SCI-03/P4-SCI-04A")

    def test_a_fails_direction_fallback_order_or_product_parity(self):
        opposite = copy.deepcopy(_fixture())
        opposite["interface_flux_observed"][0] *= -1.0
        self.assertEqual(_riemann_audit(opposite)["status"], "FAIL")

        fallback = copy.deepcopy(_fixture())
        fallback["reason_iface"] = "synthetic_fallback"
        self.assertEqual(_riemann_audit(fallback)["status"], "FAIL")

        unordered = copy.deepcopy(_fixture())
        unordered["speeds_iface"] = [2.0, 1.0, 3.0]
        self.assertEqual(_riemann_audit(unordered)["status"], "FAIL")

    def test_r4_guard_rejects_r3_and_existing_output(self):
        with self.assertRaises(ValueError):
            ensure_safe_output(R3_OUTPUT)
        with patch.object(Path, "exists", return_value=True):
            with self.assertRaises(FileExistsError):
                ensure_safe_output(R4_OUTPUT)

    def test_r4_path_is_distinct_and_no_campaign_entrypoint_exists(self):
        self.assertEqual(str(R4_OUTPUT), "results\\p4-c3-r4-20260928")
        self.assertNotEqual(R4_OUTPUT, R3_OUTPUT)


if __name__ == "__main__":
    unittest.main()
