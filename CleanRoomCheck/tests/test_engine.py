import unittest
from datetime import date
from tests.helpers import base_model, fact, edge

class EngineTests(unittest.TestCase):
    def evaluate(self,m=None,as_of='2026-10-14',age=90):
        try:
            from cleanroomcheck.engine import evaluate
        except ImportError:
            self.fail('evidence-aware rule engine is not implemented')
        return evaluate(m or base_model(),date.fromisoformat(as_of),age)

    def finding(self,model,rid,**kwargs):
        result=self.evaluate(model,**kwargs)
        return next(x for x in result['findings'] if x['rule_id']==rid)

    def test_separate_verified_fixture_satisfies_non_m365_checks(self):
        r=self.evaluate()
        self.assertGreaterEqual(len(r['findings']),30)
        self.assertEqual(r['summary']['FAILED'],0)
        self.assertEqual(r['summary']['UNKNOWN'],0)
        self.assertEqual(r['overall'],'MODEL_CHECKS_SATISFIED')
        self.assertTrue(r['project']['demo'])

    def test_missing_claim_is_unknown_not_pass(self):
        m=base_model(); del m['assessments'][0]['facts']['dedicated_admin_device']
        self.assertEqual(self.finding(m,'CRC-ID-002')['status'],'UNKNOWN')

    def test_self_reported_true_cannot_pass(self):
        m=fact(base_model(),'dedicated_admin_device',True,['say'])
        self.assertEqual(self.finding(m,'CRC-ID-002')['status'],'UNKNOWN')

    def test_false_without_evidence_is_flagged_as_input_only(self):
        m=fact(base_model(),'dedicated_admin_device',False,[])
        f=self.finding(m,'CRC-ID-002')
        self.assertEqual(f['status'],'FAILED'); self.assertEqual(f['assurance'],'none')

    def test_freshness_boundary_future_and_stale(self):
        for observed,as_of,expected in [('2026-10-14','2026-10-14','PASSED'),('2026-07-16','2026-10-14','PASSED'),('2026-07-15','2026-10-14','UNKNOWN'),('2026-10-15','2026-10-14','UNKNOWN')]:
            m=base_model(); m['evidence'][0]['collected_at']=observed
            with self.subTest(observed=observed): self.assertEqual(self.finding(m,'CRC-ID-002',as_of=as_of)['status'],expected)

    def test_config_evidence_cannot_stand_in_for_restore_test(self):
        m=fact(base_model(),'restore_tested',True,['cfg'])
        self.assertEqual(self.finding(m,'CRC-REC-002')['status'],'UNKNOWN')

    def test_every_condition_needs_its_own_evidence(self):
        m=fact(base_model(),'external_dependencies_tested',True,[])
        self.assertEqual(self.finding(m,'CRC-VAL-008')['status'],'UNKNOWN')

    def test_same_tenant_admin_path_detected(self):
        m=base_model(); m['nodes'][3]['tenant']='prod-tenant'
        f=self.finding(m,'CRC-ID-001')
        self.assertEqual(f['status'],'FAILED'); self.assertTrue(f['paths'])
        self.assertEqual(f['paths'][0][0]['inferred'],'AZURE_GLOBAL_ADMIN')

    def test_cross_tenant_native_vm_restore_rejected(self):
        m=fact(base_model(),'restore_method','azure_vm_native')
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'FAILED')

    def test_native_same_tenant_still_needs_support_evidence(self):
        m=fact(base_model(),'restore_method','azure_vm_native'); m['nodes'][3]['tenant']='prod-tenant'
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'PASSED')
        fact(m,'restore_supported',None,[])
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'UNKNOWN')

    def test_native_restore_missing_tenant_is_unknown(self):
        m=fact(base_model(),'restore_method','azure_vm_native'); del m['nodes'][3]['tenant']
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'UNKNOWN')

    def test_key_risk_does_not_turn_locked_storage_into_unlocked(self):
        m=base_model(); edge(m,'prod-sub','key','can_disable')
        self.assertEqual(self.finding(m,'CRC-KEY-001')['status'],'FAILED')
        self.assertEqual(self.finding(m,'CRC-BAK-001')['status'],'PASSED')

    def test_control_graph_incomplete_no_path_is_unknown(self):
        m=fact(base_model(),'control_graph_complete',None,[])
        self.assertEqual(self.finding(m,'CRC-ID-001')['status'],'UNKNOWN')
        self.assertEqual(self.finding(m,'CRC-KEY-001')['status'],'UNKNOWN')

    def test_network_path_is_not_authority(self):
        m=base_model(); edge(m,'prod-sub','rec-sub','network_reach')
        self.assertEqual(self.finding(m,'CRC-NET-001')['status'],'FAILED')
        self.assertEqual(self.finding(m,'CRC-ID-001')['status'],'PASSED')

    def test_lock_modes_require_irreversibility(self):
        for value in ['none','governance','azure_unlocked']:
            with self.subTest(value=value):
                self.assertEqual(self.finding(fact(base_model(),'immutable_mode',value),'CRC-BAK-001')['status'],'FAILED')

    def test_other_locked_requires_manual_review_not_automatic_pass(self):
        m=fact(base_model(),'immutable_mode','other_locked')
        self.assertEqual(self.finding(m,'CRC-BAK-001')['status'],'UNKNOWN')

    def test_protection_expired_or_expires_today_not_pass(self):
        for day in ['2026-10-13','2026-10-14']:
            self.assertEqual(self.finding(fact(base_model(),'protection_until',day),'CRC-BAK-002')['status'],'FAILED')

    def test_retention_compares_business_requirement_not_universal_constant(self):
        m=fact(base_model(),'retention_days',10)
        self.assertEqual(self.finding(m,'CRC-BAK-003')['status'],'FAILED')
        fact(m,'required_retention_days',5)
        self.assertEqual(self.finding(m,'CRC-BAK-003')['status'],'PASSED')

    def test_missing_required_retention_not_guessed(self):
        m=fact(base_model(),'required_retention_days',None)
        self.assertEqual(self.finding(m,'CRC-BAK-003')['status'],'UNKNOWN')

    def test_rto_and_rpo_measured_evidence(self):
        for field,value,rid in [('measured_rto_hours',10,'CRC-REC-003'),('measured_data_loss_hours',25,'CRC-REC-004')]:
            m=fact(base_model(),field,value,['test'])
            self.assertEqual(self.finding(m,rid)['status'],'FAILED')

    def test_m365_not_equated_to_vm_restore(self):
        m=base_model(); a=m['assessments'][0]; a['provider']='m365'; a['workload']='m365'
        fact(m,'restore_method','m365_backup'); fact(m,'m365_identity_plan',None,[])
        self.assertEqual(self.finding(m,'CRC-M365-002')['status'],'UNKNOWN')
        fact(m,'restore_method','azure_vm_native')
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'FAILED')

    def test_m365_checks_not_applicable_to_vm(self):
        self.assertEqual(self.finding(base_model(),'CRC-M365-001')['status'],'NOT_APPLICABLE')

    def test_no_input_mutation_and_reproducible_results(self):
        import copy
        m=base_model(); original=copy.deepcopy(m)
        self.assertEqual(self.evaluate(m),self.evaluate(m)); self.assertEqual(m,original)

    def test_different_scenarios_produce_different_paths(self):
        m=base_model(); m['nodes'][3]['tenant']='prod-tenant'
        m['scenarios'].append({'id':'vault-only','name':'保管先のみ侵害','compromised':['vault']})
        findings=[x for x in self.evaluate(m)['findings'] if x['rule_id']=='CRC-ID-001']
        self.assertEqual([x['status'] for x in findings],['FAILED','PASSED'])

    def test_invalid_age_rejected(self):
        from cleanroomcheck.model import ModelError
        for age in [-1,True,0,100001]:
            with self.subTest(age=age):
                with self.assertRaises(ModelError): self.evaluate(age=age)

    def test_lock_finalization_required_even_in_compliance_mode(self):
        m=base_model(); fact(m,'lock_finalized',False)
        self.assertEqual(self.finding(m,'CRC-BAK-001')['status'],'FAILED')
        fact(m,'lock_finalized',None,[])
        self.assertEqual(self.finding(m,'CRC-BAK-001')['status'],'UNKNOWN')

    def test_provider_key_with_customer_key_node_is_ambiguous(self):
        m=fact(base_model(),'key_management','provider')
        self.assertEqual(self.finding(m,'CRC-KEY-001')['status'],'UNKNOWN')

    def test_m365_builtin_cross_tenant_not_assumed_supported(self):
        m=base_model(); a=m['assessments'][0]; a['provider']='m365'; a['workload']='m365'
        fact(m,'restore_method','m365_backup')
        self.assertEqual(self.finding(m,'CRC-REC-001')['status'],'UNKNOWN')

    def test_report_snapshot_cannot_change_when_input_is_edited(self):
        import copy
        m=base_model(); result=self.evaluate(m); snapshot=copy.deepcopy(result)
        m['scenarios'][0]['compromised']=['vault']
        m['nodes'][0]['label']='Changed'
        m['evidence'][0]['reference']='Changed'
        self.assertEqual(result,snapshot)

    def test_management_control_alone_does_not_prove_network_reachability(self):
        m=base_model();edge(m,'prod-sub','rec-sub','controls')
        self.assertEqual(self.finding(m,'CRC-ID-001')['status'],'FAILED')
        self.assertEqual(self.finding(m,'CRC-NET-001')['status'],'PASSED')
