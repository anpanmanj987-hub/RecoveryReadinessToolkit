import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import base_model

class InputTests(unittest.TestCase):
    def api(self):
        try:
            from cleanroomcheck.io import load_model, export_csv_bundle
            from cleanroomcheck.model import ModelError
        except ImportError:
            self.fail('safe input adapters are not implemented')
        return load_model, export_csv_bundle, ModelError

    def test_json_round_trip(self):
        load,_,_=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.json'; p.write_text(json.dumps(base_model()),encoding='utf-8')
            self.assertEqual(load(p),base_model())

    def test_duplicate_json_key_rejected(self):
        load,_,error=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.json'; p.write_text('{"a":1,"a":2}',encoding='utf-8')
            with self.assertRaises(error): load(p)

    def test_nonfinite_json_rejected(self):
        load,_,error=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.json'; p.write_text('{"x": NaN}',encoding='utf-8')
            with self.assertRaises(error): load(p)

    def test_csv_bundle_round_trip(self):
        load,export,_=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bundle'; export(base_model(),p)
            self.assertEqual(load(p),base_model())

    def test_csv_duplicate_fact_rejected(self):
        load,export,error=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bundle'; export(base_model(),p)
            path=p/'facts.csv'; lines=path.read_text(encoding='utf-8-sig').splitlines()
            path.write_text('\n'.join(lines+[lines[1]]),encoding='utf-8')
            with self.assertRaises(error): load(p)

    def test_yaml_safe_input_and_unsafe_tags(self):
        load,_,error=self.api()
        try: import yaml
        except ImportError: self.skipTest('optional PyYAML not installed')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.yaml'; p.write_text(yaml.safe_dump(base_model(),allow_unicode=True),encoding='utf-8')
            self.assertEqual(load(p),base_model())
            for text in ['x: !!python/object/apply:os.system ["echo unsafe"]', 'x: &a [1]\ny: *a', 'x: 1\nx: 2']:
                p.write_text(text,encoding='utf-8')
                with self.assertRaises(error): load(p)

    def test_deep_or_large_input_rejected(self):
        load,_,error=self.api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.json'
            for text in ['['*60+'0'+']'*60, ' '*2100000]:
                p.write_text(text,encoding='utf-8')
                with self.assertRaises(error): load(p)
