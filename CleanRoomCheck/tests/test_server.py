import http.client
import json
import re
import threading
import unittest
from tests.helpers import base_model

class ServerTests(unittest.TestCase):
    def setUp(self):
        try:
            from cleanroomcheck.server import make_server
        except ImportError:
            self.fail('loopback-only UI server is not implemented')
        self.server=make_server(0); self.port=self.server.server_address[1]
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);self.thread.start()

    def tearDown(self):
        if hasattr(self,'server'):
            self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)

    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request(method,path,body=body,headers=headers or {})
        response=conn.getresponse();text=response.read().decode('utf-8');status=response.status;hdr=dict(response.getheaders());conn.close()
        return status,text,hdr

    def token(self):
        status,text,_=self.request('GET','/')
        self.assertEqual(status,200)
        return re.search(r'name="crc-token" content="([^"]+)"',text).group(1)

    def post(self,payload,extra=None,path='/api/evaluate'):
        headers={'Content-Type':'application/json','X-CRC-Token':self.token(),'Origin':f'http://127.0.0.1:{self.port}'}
        headers.update(extra or {})
        return self.request('POST',path,json.dumps(payload),headers)

    def test_binds_only_loopback(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')

    def test_index_security_headers(self):
        status,text,headers=self.request('GET','/')
        self.assertEqual(status,200);self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertIn('CleanRoomCheck',text)

    def test_host_rebinding_blocked(self):
        status,_,_=self.request('GET','/',headers={'Host':'attacker.example'})
        self.assertEqual(status,403)

    def test_missing_token_blocked(self):
        status,_,_=self.request('POST','/api/evaluate',json.dumps({'model':base_model()}),{'Content-Type':'application/json'})
        self.assertEqual(status,403)

    def test_cross_origin_blocked_even_with_token(self):
        self.assertEqual(self.post({'model':base_model()},{'Origin':'https://attacker.example'})[0],403)

    def test_form_content_type_blocked(self):
        self.assertEqual(self.post({'model':base_model()},{'Content-Type':'text/plain'})[0],415)

    def test_eval_uses_exact_same_core(self):
        from cleanroomcheck.engine import evaluate
        from datetime import date
        status,text,_=self.post({'model':base_model(),'as_of':'2026-10-14'})
        self.assertEqual(status,200,text)
        data=json.loads(text)
        self.assertEqual(data['result'],evaluate(base_model(),date(2026,10,14)))
        self.assertIn('CleanRoomCheck',data['html'])

    def test_invalid_model_returns_error_not_stack_trace(self):
        status,text,_=self.post({'model':{'invalid':True}})
        self.assertEqual(status,400);self.assertNotIn('Traceback',text)

    def test_path_traversal_not_served(self):
        for path in ['/../pyproject.toml','/assets/../model.py','/.git/config']:
            self.assertEqual(self.request('GET',path)[0],404)

    def test_bootstrap_includes_five_templates(self):
        status,text,_=self.request('GET','/api/bootstrap',headers={'X-CRC-Token':self.token()})
        self.assertEqual(status,200);self.assertEqual(len(json.loads(text)['examples']),5)

    def test_validate_endpoint(self):
        status,text,_=self.post({'model':base_model()},path='/api/validate')
        self.assertEqual(status,200);self.assertTrue(json.loads(text)['valid'])

    def test_large_request_rejected_without_reading_body(self):
        headers={'Content-Type':'application/json','X-CRC-Token':self.token(),'Content-Length':'999999999'}
        self.assertEqual(self.request('POST','/api/evaluate',body='',headers=headers)[0],413)

    def test_raw_json_validation_rejects_duplicate_keys(self):
        text=json.dumps(base_model()).replace('"demo": true','"demo": true, "demo": false')
        status,body,_=self.post({'model_json':text},path='/api/validate')
        self.assertEqual(status,400);self.assertIn('重複',json.loads(body)['error'])

    def test_raw_json_returns_validated_model(self):
        status,body,_=self.post({'model_json':json.dumps(base_model())},path='/api/validate')
        self.assertEqual(status,200,body);self.assertEqual(json.loads(body)['model'],base_model())

    def test_both_model_forms_rejected(self):
        status,_,_=self.post({'model':base_model(),'model_json':json.dumps(base_model())},path='/api/validate')
        self.assertEqual(status,400)

    def test_malformed_absolute_uri_cannot_crash_handler(self):
        self.assertEqual(self.request('GET','http://[',headers={'Host':f'127.0.0.1:{self.port}'})[0],404)
