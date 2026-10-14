import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from tests.helpers import base_model, fact

ROOT=Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def test_repository_contains_publishable_metadata_and_guides(self):
        for name in ['README.md','LICENSE','SECURITY.md','CONTRIBUTING.md','CHANGELOG.md','pyproject.toml','docs/MODEL.md','docs/RULES.md','docs/REFERENCE_PATTERNS.md','docs/LIMITATIONS.md','docs/model.schema.json','.github/workflows/tests.yml']:
            with self.subTest(name=name):self.assertTrue((ROOT/name).is_file(),name)

    def test_catalogue_has_unique_ids_and_valid_sources(self):
        from cleanroomcheck.catalog import RULES,LABELS,load_sources
        from cleanroomcheck.model import FIELDS
        self.assertEqual(len(RULES),32);self.assertEqual(len({r['id'] for r in RULES}),32)
        self.assertEqual(set(FIELDS),set(LABELS))
        sources=load_sources();ids={s['id'] for s in sources}
        self.assertEqual(len(ids),10)
        for rule in RULES:
            self.assertTrue(set(rule['source_ids'])<=ids)
            self.assertTrue(set(rule['fields'])<=set(FIELDS))
        for source in sources:self.assertTrue(source['url'].startswith('https://'))

    def test_missing_conditions_cannot_satisfy_any_rule(self):
        from cleanroomcheck.catalog import RULES
        from cleanroomcheck.engine import evaluate
        for rule in RULES:
            with self.subTest(rule=rule['id']):
                m=base_model()
                if rule['category']=='M365':m['assessments'][0].update(provider='m365',workload='m365')
                for field in rule['fields']:fact(m,field,None,[])
                finding=next(f for f in evaluate(m,date(2026,10,14))['findings'] if f['rule_id']==rule['id'])
                self.assertEqual(finding['status'],'UNKNOWN')

    def test_public_examples_equal_packaged_examples(self):
        from cleanroomcheck.cli import TEMPLATES,example
        for name in TEMPLATES:
            self.assertEqual(example(name),json.loads((ROOT/'examples'/f'{name}.json').read_text(encoding='utf-8')))

    def test_demo_preserves_unresolved_items(self):
        from cleanroomcheck.cli import example
        from cleanroomcheck.engine import evaluate
        from cleanroomcheck.compare import compare_results
        before=evaluate(example('azure-risky'),date(2026,10,14));after=evaluate(example('azure-improved'),date(2026,10,14))
        self.assertEqual(before['summary'],{'PASSED':13,'FAILED':35,'UNKNOWN':36,'NOT_APPLICABLE':12})
        self.assertEqual(after['summary'],{'PASSED':45,'FAILED':0,'UNKNOWN':39,'NOT_APPLICABLE':12})
        self.assertEqual(compare_results(before,after)['summary']['resolved_in_model'],35)
