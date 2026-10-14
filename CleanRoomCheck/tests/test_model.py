import unittest
from tests.helpers import base_model, fact

class ModelTests(unittest.TestCase):
    def validator(self):
        try:
            from cleanroomcheck.model import validate_model, ModelError
        except ImportError:
            self.fail('strict model validation is not implemented')
        return validate_model, ModelError

    def test_minimum_valid_model(self):
        validate, _ = self.validator()
        m = base_model()
        self.assertEqual(validate(m), m)

    def test_unknown_fields_and_typos_rejected(self):
        validate, error = self.validator()
        for target in ['top', 'fact', 'node']:
            with self.subTest(target=target):
                m = base_model()
                if target == 'top': m['accidental_typo'] = 1
                if target == 'fact': fact(m, 'independant_identity', True)
                if target == 'node': m['nodes'][0]['tennant'] = 'x'
                with self.assertRaises(error): validate(m)

    def test_duplicate_ids_rejected(self):
        validate, error = self.validator()
        for section in ['nodes', 'evidence', 'scenarios', 'assessments']:
            with self.subTest(section=section):
                m = base_model(); m[section].append(m[section][0].copy())
                with self.assertRaises(error): validate(m)

    def test_dangling_references_rejected(self):
        validate, error = self.validator()
        mutations = [lambda m: m['assessments'][0].update(recovery_node='absent'),
                     lambda m: m['nodes'][3].update(tenant='absent'),
                     lambda m: m['scenarios'][0].update(compromised=['absent']),
                     lambda m: fact(m, 'independent_identity', True, ['absent'])]
        for mutate in mutations:
            m=base_model(); mutate(m)
            with self.assertRaises(error): validate(m)

    def test_fact_types_are_strict(self):
        validate, error = self.validator()
        for field, value in [('independent_identity','false'), ('retention_days',True), ('retention_days',-1), ('rto_hours',float('inf')), ('protection_until','2026-02-30'), ('immutable_mode','magic'), ('restore_method', [])]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(error): validate(fact(base_model(),field,value))

    def test_null_is_allowed_as_unknown(self):
        validate, _ = self.validator()
        validate(fact(base_model(), 'retention_days', None, []))

    def test_empty_scenarios_and_assessments_rejected(self):
        validate,error = self.validator()
        for section in ['scenarios','assessments']:
            m=base_model(); m[section]=[]
            with self.assertRaises(error): validate(m)

    def test_admin_inference_requires_compromised_azure_tenant(self):
        validate,error = self.validator()
        for ids in [['rec-tenant'],['prod-sub']]:
            m=base_model(); m['scenarios'][0]['azure_global_admin_tenants']=ids
            with self.assertRaises(error): validate(m)

    def test_wrong_key_reference_type_rejected(self):
        validate,error=self.validator()
        m=base_model(); m['assessments'][0]['key_node']='logs'
        with self.assertRaises(error): validate(m)

    def test_schema_version_and_duplicate_claim_evidence_rejected(self):
        validate,error=self.validator()
        m=base_model(); m['schema_version']='2.0'
        with self.assertRaises(error): validate(m)
        with self.assertRaises(error): validate(fact(base_model(),'independent_identity',True,['cfg','cfg']))
