import math
import unittest

from motorsim.p8_performance import (P8_ANCHORS, cycle_duration_s,
                                      indicated_metrics, omega_deg_s,
                                      validate_p8_rpm, work_from_pressure_volume)
from motorsim.project import ProjectError
from motorsim.p5c import make_p5c_fixture
from motorsim.p8_performance import model_geometry_callback
from motorsim.coupling import ChamberState
from motorsim.exhaust_port import port_flux
from motorsim.gas1d.eos import IdealGas


class P8ContractTests(unittest.TestCase):
    def test_domain_and_timing(self):
        self.assertEqual(P8_ANCHORS, (2500, 5000, 8000, 11000, 15000))
        self.assertEqual(omega_deg_s(2500), 15000.0)
        self.assertEqual(omega_deg_s(15000), 90000.0)
        self.assertEqual(cycle_duration_s(2500), 60 / 2500)
        for rpm in (2499, 15001, 2500.0, True):
            with self.assertRaises(ProjectError):
                validate_p8_rpm(rpm)

    def test_work_sign_and_formulas(self):
        expansion = work_from_pressure_volume((100000, 100000), (1e-4, 2e-4))
        compression = work_from_pressure_volume((100000, 100000), (2e-4, 1e-4))
        self.assertGreater(expansion, 0)
        self.assertLess(compression, 0)
        m = indicated_metrics(12.0, 6000, 2.5e6)
        self.assertEqual(m["P_indicated_W"], 1200.0)
        self.assertAlmostEqual(m["T_indicated_Nm"], 12 / (2 * math.pi))

    def test_geometry_callback_updates_both_ssprk_stages(self):
        seen = []
        def geometry(angle):
            seen.append(angle)
            volume = 0.01 + angle * 1e-6
            return {'volumes': (0.001, volume, volume, 0.002),
                    'volume_rates': (0.0, 0.0),
                    'areas': (0.0, 0.0, 0.0, 0.0)}
        fixture = make_p5c_fixture(port_area=0.0)
        fixture.geometry_callback = geometry
        fixture.core.geometry_callback = geometry
        fixture.step(0.1, angle=12.0)
        self.assertEqual(seen[:3], [11.9, 11.9, 11.9])
        self.assertIn(12.0, seen)
        self.assertAlmostEqual(fixture.history[-1]['stage_states'][0][1][4], 0.0100119)
        self.assertAlmostEqual(fixture.history[-1]['stage_states'][2][1][4], 0.010012)

    def test_callback_uses_authoritative_crankcase_and_cylinder_slots(self):
        def geometry(angle):
            return {'volumes': (0.11, 0.21 + angle * 1e-6,
                                0.31 + angle * 1e-6, 0.41),
                    'volume_rates': (0.0, 0.0),
                    'areas': (0.0, 0.0, 0.0, 0.0)}
        fixture = make_p5c_fixture(port_area=0.0)
        fixture.geometry_callback = geometry
        fixture.core.geometry_callback = geometry
        fixture.step(0.1, angle=12.0)
        q0, _, qn = fixture.history[-1]['stage_states']
        self.assertAlmostEqual(q0[0][4], 0.21 + 11.9e-6)
        self.assertAlmostEqual(q0[1][4], 0.31 + 11.9e-6)
        self.assertAlmostEqual(qn[0][4], 0.21 + 12e-6)
        self.assertAlmostEqual(qn[1][4], 0.31 + 12e-6)

    def test_model_geometry_area_mapping_is_direct(self):
        class FakeModel:
            case = type('Case', (), {'project_geometry': object()})()
            def geometry(self, angle):
                return ((1, 2, 3, 4), (5, 6, 7, 8),
                        (10, 11, 12, 13, 14, 15))
        callback = model_geometry_callback(FakeModel())
        self.assertEqual(callback(0)['areas'], (11, 12, 13, 14))

    def test_dynamic_exhaust_area_is_capped_by_fixed_pipe(self):
        eos = IdealGas()
        chamber = ChamberState(1e-5, 100.0, 0.0, 1e-4)
        pipe = (1.0, 0.0, 100000.0, 0.0)
        face = port_flux(chamber, pipe, 3e-4, 1e-4, eos=eos)
        self.assertEqual(face['area'], 1e-4)


if __name__ == "__main__":
    unittest.main()
