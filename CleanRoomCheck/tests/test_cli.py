import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import base_model, fact

class CliTests(unittest.TestCase):
    def api(self):
        try:
            from cleanroomcheck.cli import main
        except ImportError:
            self.fail('CLI is not implemented')
        return main

    def run_cli(self,args):
        main=self.api(); out=io.StringIO(); err=io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=main(args)
        return code,out.getvalue(),err.getvalue()

    def test_validate_command(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json'; p.write_text(json.dumps(base_model()),encoding='utf-8')
            code,out,err=self.run_cli(['validate',str(p)])
            self.assertEqual(code,0,err); self.assertIn('VALID',out)

    def test_report_creation_and_exit_codes(self):
        cases=[(base_model(),0),(fact(base_model(),'dedicated_admin_device',False),1),(fact(base_model(),'dedicated_admin_device',None,[]),1)]
        for model,expected in cases:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'input.json'; p.write_text(json.dumps(model),encoding='utf-8'); output=Path(d)/'review'
                code,out,err=self.run_cli(['check',str(p),'--out',str(output),'--as-of','2026-10-14'])
                self.assertEqual(code,expected,err)
                for name in ['report.html','report.json','questions.csv','verification.csv']:
                    self.assertTrue((output/name).is_file(),name)

    def test_input_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json'; original=json.dumps(base_model()); p.write_text(original,encoding='utf-8')
            code,_,err=self.run_cli(['check',str(p),'--out',d,'--as-of','2026-10-14'])
            self.assertEqual(code,2); self.assertEqual(p.read_text(),original)

    def test_output_directory_cannot_reuse_old_results(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json'; p.write_text(json.dumps(base_model()),encoding='utf-8')
            out=Path(d)/'output'; out.mkdir()
            self.assertEqual(self.run_cli(['check',str(p),'--out',str(out)])[0],2)

    def test_invalid_input_no_stack_trace(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json'; p.write_text('{bad',encoding='utf-8')
            code,out,err=self.run_cli(['validate',str(p)])
            self.assertEqual(code,2); self.assertNotIn('Traceback',err)

    def test_fail_on_never_does_not_hide_findings(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json'; p.write_text(json.dumps(fact(base_model(),'dedicated_admin_device',False)),encoding='utf-8')
            code,out,err=self.run_cli(['check',str(p),'--out',str(Path(d)/'out'),'--as-of','2026-10-14','--fail-on','never'])
            self.assertEqual(code,0,err); self.assertIn('FAILED',out)
