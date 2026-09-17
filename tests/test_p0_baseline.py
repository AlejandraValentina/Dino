"""Contratos P0 y evidencia histórica; sin nuevas integraciones en tests."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dev_orchestrator import p0_campaign as p
from dev_orchestrator.contracts import read_json,load_phase
from dev_orchestrator.p0_finalize import validate_review,final_label,preflight_destinations,preserve,rollback_close


class P0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.historical=read_json(p.ROOT/'results/frontera-baja-2t-20260917/3000.json')

    def test_only_p0_enabled_without_repair_or_chaining(self):
        config=read_json(p.ROOT/'dev_orchestrator/config.json')
        _,phase=load_phase(p.ROOT,'P0',config)
        self.assertTrue(phase['enabled']);self.assertTrue(phase['human_gate'])
        self.assertEqual(phase['max_repair_attempts'],0)
        for i in range(1,10): self.assertFalse(load_phase(p.ROOT,f'P{i}',config)[1]['enabled'])
        self.assertEqual(p.MAIN_RPMS,tuple(range(2500,15001,500)))
        self.assertEqual(len(p.MAIN_RPMS),26)
        self.assertIn('motorsim/',phase['forbidden_paths'])

    def test_existing_contract_rejects_nonconverged_nonfinite_invariant_balance(self):
        self.assertTrue(p.point_passed(self.historical['result']))
        for defect in ('converged','nan','F','balance'):
            result=deepcopy(self.historical['result'])
            if defect=='converged':result['converged']=False
            if defect=='nan':result['cycles'][-1]['W_C_J']=float('nan')
            if defect=='F':result['last_two_cycles'][0][0]['state'][2]=-1e-30
            if defect=='balance':result['cycles'][-1]['independent']['global']['normalized_m_u_f'][2]=.00101
            self.assertFalse(p.point_passed(result),defect)

    def test_exact_historical_only_time_ignored(self):
        document=deepcopy(self.historical);document['result']['seconds']+=10
        self.assertTrue(p.compare_historical(3000,document)['passed'])
        document['result']['cycles'][-1]['W_C_J']+=1e-12
        self.assertFalse(p.compare_historical(3000,document)['passed'])

    def test_main_gate_no_skips_and_stress_not_controlling(self):
        rows=[dict(rpm=r,passed=True) for r in p.MAIN_RPMS]
        regression=[dict(rpm=r,passed=True) for r in p.HISTORICAL_RPMS]
        self.assertEqual(p.main_gate(rows,regression),'ELIGIBLE_FOR_REVIEW_AND_FREEZE')
        self.assertEqual(p.main_gate(rows[:-1],regression),'P0_BLOCKED_CONTINUOUS_DOMAIN')
        rows[3]['passed']=False
        self.assertEqual(p.main_gate(rows,regression),'P0_BLOCKED_CONTINUOUS_DOMAIN')
        rows[3]['passed']=True;regression[0]['passed']=False
        self.assertEqual(p.main_gate(rows,regression),'P0_BLOCKED_REGRESSION')
        regression[0]['passed']=True
        self.assertEqual(final_label(dict(gate='PASS',scope_violations=[]),dict(rows=rows,regressions=regression,stress_state='HIGH_RPM_STRESS_LIMIT_OBSERVED')),'P0_PASS_BASELINE_FROZEN')

    def test_campaign_visits_all_and_does_not_stress_after_failure(self):
        calls=[]
        def fake(base,rpm,run_dir):
            calls.append(rpm)
            return dict(rpm=rpm,passed=rpm!=4000,integration_seconds=1.,wall_seconds=1.,
                completed_cycles=1,rejected_steps=0,minimum_step_deg=.001),{}
        with tempfile.TemporaryDirectory() as temporary:
            run_dir=Path(temporary);(run_dir/'artifacts').mkdir()
            with patch.object(p,'execute_point',side_effect=fake),patch.object(p,'snapshot',return_value={'commit':'test'}),patch.object(p,'compare_historical',side_effect=lambda rpm,doc:dict(rpm=rpm,passed=True)),patch('builtins.print'):
                p.campaign(run_dir)
            data=read_json(run_dir/'artifacts/campaign.json')
            self.assertEqual(calls,list(p.MAIN_RPMS));self.assertEqual(data['stress'],[])
            self.assertEqual(data['first_failure']['rpm'],4000)
            self.assertEqual(data['last_contiguous_pass_rpm'],3500)

    def test_stress_failure_does_not_block_main(self):
        calls=[]
        def fake(base,rpm,run_dir):
            calls.append(rpm)
            return dict(rpm=rpm,passed=rpm!=18000,integration_seconds=1.,wall_seconds=1.,
                completed_cycles=1,rejected_steps=0,minimum_step_deg=.001),{}
        with tempfile.TemporaryDirectory() as temporary:
            run_dir=Path(temporary);(run_dir/'artifacts').mkdir()
            with patch.object(p,'execute_point',side_effect=fake),patch.object(p,'snapshot',return_value={'commit':'test'}),patch.object(p,'compare_historical',side_effect=lambda rpm,doc:dict(rpm=rpm,passed=True)),patch('dev_orchestrator.p0_plots.render'),patch('builtins.print'):
                p.campaign(run_dir)
            data=read_json(run_dir/'artifacts/campaign.json')
            self.assertEqual(calls,list(p.MAIN_RPMS+p.STRESS_RPMS))
            self.assertEqual(data['stress_state'],'HIGH_RPM_STRESS_LIMIT_OBSERVED')
            self.assertEqual(data['scientific_gate'],'ELIGIBLE_FOR_REVIEW_AND_FREEZE')

    def test_review_must_bind_evidence_and_be_independent(self):
        path=p.ROOT/'dev_orchestrator/examples/dummy-pass/evidence.json'
        data=read_json(path);data['phase_id']='P0'
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'evidence.json';target.write_text(json.dumps(data),encoding='utf-8')
            envelope=dict(run_id=data['run_id'],evidence_sha256=p.sha(target),review=dict(status='PASS',findings=[],blocking_findings=[],scientific_change_required=False,notes='Read-only external review.',kind='independent'))
            self.assertEqual(validate_review(envelope,target)[1]['kind'],'independent')
            envelope['review']['kind']='dummy_stub'
            with self.assertRaises(ValueError):validate_review(envelope,target)
            envelope['review']['kind']='independent';envelope['evidence_sha256']='wrong'
            with self.assertRaises(ValueError):validate_review(envelope,target)

    def test_finalize_preflight_does_not_create_marker_and_preserves_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);existing=root/'baseline.json';existing.write_bytes(b'user work')
            with self.assertRaises(FileExistsError):preflight_destinations(root,('baseline.json','baseline.md'))
            self.assertEqual(list(root.iterdir()),[existing])
            backup=root/'pre-review.json';preserve(backup,b'original');preserve(backup,b'original')
            with self.assertRaises(ValueError):preserve(backup,b'changed')
            self.assertEqual(backup.read_bytes(),b'original')

    def test_failed_close_restores_original_evidence_and_only_own_new_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'artifacts').mkdir();(root/'docs').mkdir()
            for name in ('evidence.json','summary.md'):
                (root/'artifacts'/('pre-review-'+name)).write_bytes(b'original')
                (root/name).write_bytes(b'partial report')
            owned=root/'docs/baseline.json';foreign=root/'docs/baseline.md'
            for path in (owned,foreign):
                (root/'artifacts'/path.name).write_bytes(b'our data');path.write_bytes(b'our data')
            foreign.write_bytes(b'concurrent change')
            rollback_close(root,[owned,foreign])
            self.assertFalse(owned.exists());self.assertEqual(foreign.read_bytes(),b'concurrent change')
            self.assertEqual((root/'evidence.json').read_bytes(),b'original')


if __name__=='__main__':unittest.main()
