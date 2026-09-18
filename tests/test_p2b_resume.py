import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dev_orchestrator import p2b_resume as p
from dev_orchestrator.p2b_campaign import run_case


class ResumeTests(unittest.TestCase):
    def test_only_completed_identical_records_reused(self):
        records,origins=p.load_reusable(p.PREVIOUS,p.source_hashes())
        self.assertEqual(len(records),8)
        self.assertNotIn('T04',records)
        self.assertEqual(set(records),set(origins))
        self.assertTrue(all(len(o['sha256'])==64 for o in origins.values()))

    def test_changed_solver_refuses_reuse(self):
        source=p.source_hashes();source['motorsim/gas1d/second_order.py']='changed'
        with self.assertRaisesRegex(ValueError,'source hashes differ'):p.load_reusable(p.PREVIOUS,source)

    def test_changed_inputs_change_signature(self):
        path=p.PREVIOUS/'artifacts/cases/T01_rest.json.gz'
        record=json.loads(gzip.decompress(path.read_bytes()))
        expected=p.expected_signature('T01_rest')
        self.assertEqual(p.signature(record),expected)
        record['configuration']['CFL']=.2
        self.assertNotEqual(p.signature(record),expected)

    def test_corrupt_checkpoint_evidence_rejected(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'dev_orchestrator/runs') as directory:
            folder=Path(directory);(folder/'artifacts').mkdir()
            (folder/'bad.gz').write_bytes(b'bad')
            p.write(folder/'artifacts/resume-checkpoint.json',dict(source_sha256=p.source_hashes(),cases={'T01_rest':dict(path='bad.gz',sha256='wrong')}))
            with self.assertRaisesRegex(ValueError,'artifact hash mismatch'):p.load_reusable(folder,p.source_hashes())

    def test_incomplete_t12_never_passes(self):
        records={name:dict(status='PASS') for name in ('T12_contact','T12_expansion','T12_pure0','T12_pure1')}
        gate=p.test_gate('T12',records)
        self.assertEqual(gate['status'],'PARTIAL');self.assertEqual(gate['expected_subcases'],10)

    def test_t10_requires_both_contractual_pairs(self):
        records={f'T10_{n}':dict(status='PASS',metrics=dict(density_L1=n**-1.6,fresh_L1=n**-1.6)) for n in (100,200,400,800)}
        self.assertEqual(p.test_gate('T10',records)['status'],'PASS')
        records['T10_800']['metrics']['fresh_L1']=records['T10_400']['metrics']['fresh_L1']/2
        self.assertEqual(p.test_gate('T10',records)['status'],'FAIL')
        records.pop('T10_800');self.assertEqual(p.test_gate('T10',records)['status'],'PARTIAL')

    def test_runtime_override_does_not_change_physical_arguments(self):
        with patch('dev_orchestrator.p2b_campaign.solve',side_effect=RuntimeError('captured')) as solve:
            with self.assertRaisesRegex(RuntimeError,'captured'):run_case('T04',wall_limit=300.)
            args,kwargs=solve.call_args;case=p.v.definition('T04')
            self.assertEqual(kwargs['wall_limit'],300.)
            self.assertEqual(args[2],case['end']);self.assertEqual(args[0].n,800)
            self.assertEqual(kwargs['cfl'],.4);self.assertEqual(kwargs['method'],'MUSCL_SSPRK2')


if __name__=='__main__':unittest.main()
