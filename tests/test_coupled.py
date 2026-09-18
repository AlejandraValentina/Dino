import unittest
from motorsim.coupled import solve_coupled
from motorsim.gas1d.eos import IdealGas, InvalidState
from motorsim.gas1d.mesh import uniform_mesh
from dev_orchestrator.p3_r1 import chamber


class CoupledStageTests(unittest.TestCase):
    def test_shared_stage_and_ledger(self):
        eos=IdealGas();mesh=uniform_mesh(8,.3,.0003)
        initial=[tuple(v*x for x in eos.conservative((100000/(287*300),0.,100000.,.2))) for v in mesh.volumes]
        r=solve_coupled(mesh,initial,chamber(120000,V=.0001),.00002)
        self.assertEqual(r['status'],'completed')
        self.assertEqual(len(r['traces'][0]['stages']),2)
        a,b=r['traces'][0]['stages']
        self.assertNotEqual(a['chamber'],b['chamber'])
        self.assertNotEqual(a['outward'],b['outward'])
        self.assertLess(max(max(l['normalized']) for l in r['ledger']),1e-10)
        self.assertTrue(all(l['external']==[0.,0.,0.] for l in r['ledger']))

    def test_invalid_chamber_rejected(self):
        from motorsim.coupling import ChamberState
        eos=IdealGas();mesh=uniform_mesh(2)
        q=[tuple(v*x for x in eos.conservative((1.,0.,100000.,.2))) for v in mesh.volumes]
        with self.assertRaises(InvalidState):solve_coupled(mesh,q,ChamberState(1.,-1.,.2,1.),.001)
