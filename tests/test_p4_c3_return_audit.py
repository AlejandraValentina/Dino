import unittest
import inspect

from dev_orchestrator.p4_c3_return_audit import (
    _momentum_audit, _recompute_stage, _riemann_audit, _select_return,
    _b0_audit_stage, _b1_audit_stage, _recompute_stage_b,
    classify, _physical_flux, reconstruct_external_faces,
)
from dev_orchestrator.p4_sci_04b import C2_AREA, C2_VOLUME, EOS
from dev_orchestrator.p4_sci_04b import solve_c2_one
from dev_orchestrator.reference.exact_riemann import ExactRiemann
from dev_orchestrator.reference.hllc_audit import hllc as audit_hllc


class P4C3ReturnAuditTests(unittest.TestCase):
    def test_b0_persists_used_external_faces_and_detects_mutation(self):
        result = solve_c2_one(12, 0.2, 200000.0, 400.0, 0.5,
                              100000.0, 300.0, 0.2, t_final=1e-5)
        _, info = next(item for item in result["interface_history"]
                       if "audit_stages" in item[1])
        stage = info["audit_stages"]["stage_a"]
        self.assertEqual(_b0_audit_stage(stage, result["audit_geometry"])["status"], "PASS")
        stage["external_faces"]["interface"]["right"][1] += 1.0
        self.assertEqual(_b0_audit_stage(stage, result["audit_geometry"])["status"], "FAIL")

    def test_b1_microcases_are_independent_and_frozen_by_identities(self):
        from dev_orchestrator.reference import hllc_audit
        self.assertNotIn("motorsim.gas1d.riemann", inspect.getsource(hllc_audit))
        uniform = (1.0, 0.0, 100000.0, 0.2)
        flux, waves = audit_hllc(uniform, uniform, EOS)
        self.assertEqual(flux, EOS.flux(uniform))
        self.assertLess(waves[0], waves[1])
        contact = (0.8, 0.0, 100000.0, 0.4)
        flux, waves = audit_hllc(uniform, contact, EOS)
        self.assertAlmostEqual(flux[0], 0.0, places=12)
        self.assertAlmostEqual(flux[1], 100000.0, places=8)
        self.assertAlmostEqual(flux[2], 0.0, places=6)
        shock = audit_hllc((1.0, 0., 120000., .2), (.8, 0., 100000., .4), EOS)
        rare = audit_hllc((1.0, 0., 100000., .2), (.8, 0., 120000., .4), EOS)
        self.assertAlmostEqual(shock[0][1], 109575.28957528957, places=7)
        self.assertAlmostEqual(rare[0][1], 111573.47204161249, places=7)
        wall_flux, wall_waves = audit_hllc((1.2, 35., 100000., .25),
                                           (1.2, -35., 100000., .25), EOS)
        self.assertAlmostEqual(wall_flux[0], 0.0, places=12)
        self.assertAlmostEqual(wall_flux[2], 0.0, places=5)
        self.assertAlmostEqual(wall_waves[1], 0.0, places=12)

    def test_b2_synthetic_one_cell_and_variable_area_balance(self):
        def make_stage(states, geometry, dt=0.1):
            rows = []
            for w, area in zip(states, geometry["areas"][:-1]):
                rows.append(list(area * value for value in EOS.conservative(w)))
            stage = {"dt": dt, "primitive": [list(w) for w in states],
                     "conservative": rows,
                     "chamber_state": [0.0001, 100000.0 * 0.0001 / (EOS.gamma - 1), 0.00002]}
            stage["external_faces"] = reconstruct_external_faces(states, geometry)
            stage["external_faces"]["interface"]["left"] = [1.0, 0.0, 100000.0, 0.2]
            return stage

        one_geo = {"areas": [1.0, 1.0], "faces": [0.0, 1.0], "centers": [0.5]}
        one = make_stage([(1.0, 0.0, 100000.0, 0.2)], one_geo)
        one_b = make_stage([(1.0, 0.0, 100000.0, 0.2)], one_geo)
        one["after"] = {"conservative": one["conservative"]}
        one_b["after"] = {"conservative": one_b["conservative"]}
        report = _momentum_audit([(0.1, {"audit_stages": {
            "stage_a": one, "stage_b": one_b, "after": one}})], one_geo)
        self.assertAlmostEqual(report["rows"][0]["residual"], 0.0, places=12)

        geo = {"areas": [1.0, 2.0, 3.0, 4.0], "faces": [0., 1., 2., 3.],
               "centers": [.5, 1.5, 2.5]}
        states = [(1.0, 0.0, 100000.0, 0.2)] * 3
        a = make_stage(states, geo)
        b = make_stage(states, geo)
        predicted = _recompute_stage_b(a, geo)["left"] - _recompute_stage_b(a, geo)["right"] + _recompute_stage_b(a, geo)["source"]
        b["after"] = {"conservative": [list(row) for row in b["conservative"]]}
        b["after"]["conservative"][0][1] += 0.1 * predicted
        report = _momentum_audit([(0.1, {"audit_stages": {
            "stage_a": a, "stage_b": b, "after": b}})], geo)
        self.assertAlmostEqual(report["rows"][0]["residual"], 0.0, places=10)
        self.assertGreater(report["rows"][0]["recomputed_stage_a"]["source"], 0.0)

    def test_b2_ignores_poisoned_product_flux_fields(self):
        geometry = {"areas": [1.0, 1.0], "faces": [0., 1.], "centers": [.5]}
        stage = {"dt": 0.1, "primitive": [[1., 0., 100000., .2]],
                 "conservative": [[1., 0., 250000., .2]],
                 "chamber_state": [.0001, 100000. * .0001 / (EOS.gamma - 1), .00002]}
        stage["external_faces"] = reconstruct_external_faces(stage["primitive"], geometry)
        stage["external_faces"]["interface"]["left"] = [1.0, 0.0, 100000.0, 0.2]
        info = {"audit_stages": {"stage_a": stage, "stage_b": stage,
                                 "after": {"conservative": stage["conservative"]}},
                "interface_flux_observed": [1e99] * 4,
                "momentum_face_fluxes": {"left": 1e99, "right": -1e99},
                "momentum_source_sum": 1e99}
        clean = _momentum_audit([(0.1, info)], geometry)
        self.assertEqual(clean["product_field_names_used"], [])
        self.assertNotEqual(clean["rows"][0]["recomputed_stage_a"]["left"], 1e99)
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

    def test_return_selection_uses_pre_step_sample_time(self):
        history = [(0.004, {"mass_flux": 1.0,
                            "sample_time_pre_step": 0.002})]
        selected, window = _select_return(history, 0.002)
        self.assertEqual(selected[0], 0.002)
        self.assertEqual(window, (0.001, 0.003))

        fallback_history = [(0.0025, {"mass_flux": 1.0})]
        selected, window = _select_return(fallback_history, 0.0025)
        self.assertEqual(selected[0], 0.0025)
        self.assertEqual(window, (0.00125, 0.00375))

    def test_real_step_captures_stage_a_pre_step_and_primitive_consistently(self):
        result = solve_c2_one(12, 0.2, 200000.0, 400.0, 0.5,
                              100000.0, 300.0, 0.2, t_final=1e-5)
        audited = [(time_value, info) for time_value, info in
                    result["interface_history"] if "audit_stages" in info]
        self.assertTrue(audited)
        _, info = audited[0]
        stages = info["audit_stages"]
        stage_a = stages["stage_a"]
        self.assertNotEqual(stages["stage_a"]["conservative"],
                            stages["after"]["conservative"])
        self.assertNotEqual(stages["stage_a"]["chamber_state"],
                            stages["after"]["chamber_state"])
        for row, primitive, volume in zip(
                stages["stage_a"]["conservative"],
                stages["stage_a"]["primitive"],
                result["audit_geometry"]["volumes"]):
            derived = EOS.primitive(tuple(value / volume for value in row))
            for actual, expected in zip(primitive, derived):
                self.assertAlmostEqual(actual, expected, places=12)
        expected_pressure = (EOS.gamma - 1.0) * stage_a["chamber_state"][1] / C2_VOLUME
        self.assertAlmostEqual(info["p_chamber"], expected_pressure, places=12)
        self.assertEqual(info["chamber_state"], stage_a["chamber_state"])
        self.assertEqual(info["first_cell_state"], stage_a["conservative"][0])
        self.assertEqual(info["sample_time_pre_step"], stage_a["time"])
        self.assertGreater(info["history_record_time_post_step"],
                           info["sample_time_pre_step"])

if __name__ == "__main__":
    unittest.main()
