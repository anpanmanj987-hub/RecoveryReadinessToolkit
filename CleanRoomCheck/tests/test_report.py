import copy
import csv
import io
import unittest
from datetime import date
from tests.helpers import base_model, fact

class ReportTests(unittest.TestCase):
    def result(self,m=None):
        from cleanroomcheck.engine import evaluate
        return evaluate(m or base_model(),date(2026,10,14))

    def api(self):
        try:
            from cleanroomcheck.report import render_html, questions_csv, verification_csv
        except ImportError:
            self.fail('safe HTML/CSV reporting is not implemented')
        return render_html,questions_csv,verification_csv

    def test_report_contains_disclaimer_sources_and_counts(self):
        render,_,_=self.api(); r=self.result(); text=render(r)
        for needle in ['CleanRoomCheck','架空','2026-10-14','CRC-ID-001','根拠','証跡','https://learn.microsoft.com','Content-Security-Policy']:
            self.assertIn(needle,text)
        self.assertIn(r['input_sha256'],text)

    def test_report_escapes_html_everywhere(self):
        render,_,_=self.api(); m=base_model()
        payload='</script><img src=x onerror=alert(1)>'
        m['project']['name']=payload; m['nodes'][0]['label']=payload; m['evidence'][0]['reference']=payload
        text=render(self.result(m))
        self.assertNotIn(payload,text); self.assertIn('&lt;/script&gt;',text)
        self.assertNotIn('src=x onerror=alert(1)>',text)

    def test_source_url_cannot_execute_javascript(self):
        render,_,_=self.api(); r=self.result(); r['sources'][0]['url']='javascript:alert(1)'
        self.assertNotIn('href="javascript:',render(r))

    def test_csv_formula_injection_neutralized(self):
        _,questions,_=self.api(); m=fact(base_model(),'independent_identity',False)
        m['assessments'][0]['name']=' =WEBSERVICE("https://example.invalid")'
        text=questions(self.result(m)); rows=list(csv.reader(io.StringIO(text)))
        self.assertTrue(any(cell.startswith("' =WEBSERVICE") for row in rows for cell in row))
        self.assertFalse(any(cell.startswith(' =WEBSERVICE') for row in rows for cell in row))

    def test_verification_sheet_includes_status_and_owner_columns(self):
        _,_,verification=self.api(); rows=list(csv.reader(io.StringIO(verification(self.result()))))
        self.assertIn('担当者',rows[0]); self.assertIn('実施日',rows[0]); self.assertGreater(len(rows),8)

class CompareTests(unittest.TestCase):
    def api(self):
        try:
            from cleanroomcheck.compare import compare_results, render_comparison
        except ImportError:
            self.fail('safe scope-aware comparison is not implemented')
        return compare_results,render_comparison

    def result(self,m=None):
        from cleanroomcheck.engine import evaluate
        return evaluate(m or base_model(),date(2026,10,14))

    def test_known_failure_to_pass_is_model_resolution(self):
        compare,render=self.api(); before=self.result(fact(base_model(),'dedicated_admin_device',False))
        out=compare(before,self.result())
        self.assertEqual(out['summary']['resolved_in_model'],1)
        self.assertIn('入力モデル上の解消',render(out))

    def test_failure_to_unknown_is_not_resolution(self):
        compare,_=self.api()
        out=compare(self.result(fact(base_model(),'dedicated_admin_device',False)),self.result(fact(base_model(),'dedicated_admin_device',None,[])))
        self.assertEqual(out['summary']['resolved_in_model'],0)
        self.assertEqual(out['summary']['unverified_change'],1)

    def test_removed_findings_are_scope_changes(self):
        compare,_=self.api(); before=self.result(); after=copy.deepcopy(before); after['findings']=after['findings'][1:]
        out=compare(before,after)
        self.assertEqual(out['summary']['removed'],1); self.assertEqual(out['summary']['resolved_in_model'],0)

    def test_changed_threat_model_never_counts_as_a_fix(self):
        compare,_=self.api(); m=base_model(); m['nodes'][3]['tenant']='prod-tenant'
        before=self.result(m); m['scenarios'][0]['compromised']=['vault']; m['scenarios'][0]['azure_global_admin_tenants']=[]
        out=compare(before,self.result(m))
        self.assertGreater(out['summary']['scope_changed'],0); self.assertEqual(out['summary']['resolved_in_model'],0)

    def test_unrelated_project_or_policy_date_is_rejected(self):
        compare,_=self.api()
        from cleanroomcheck.model import ModelError
        for key,value in [('as_of','2026-10-15'),('max_evidence_age_days',180),('ruleset_version','other')]:
            a=self.result(); b=copy.deepcopy(a); b[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ModelError): compare(a,b)
        a=self.result(); b=copy.deepcopy(a); b['project']['id']='unrelated'
        with self.assertRaises(ModelError): compare(a,b)
