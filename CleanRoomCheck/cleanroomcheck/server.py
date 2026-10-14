"""Ephemeral loopback UI. No model persistence, path serving, cloud calls or telemetry."""
from __future__ import annotations
import secrets
import socket
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from .catalog import RULES, field_catalog, load_sources
from .cli import TEMPLATES, example
from .engine import evaluate
from .io import dump_json, parse_json
from .model import MAX_BYTES, ModelError, obj, parse_date, validate_model
from .report import questions_csv, render_html, verification_csv

CSP="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"


class LocalServer(ThreadingHTTPServer):
    daemon_threads=True
    def get_request(self):
        sock,addr=super().get_request();sock.settimeout(5);return sock,addr


class Handler(BaseHTTPRequestHandler):
    server_version='CleanRoomCheckLocal/0.1'
    sys_version=''

    def log_message(self,fmt,*args):
        # Models, local evidence references and request paths are not logged.
        return

    def _send(self,status,body,content_type='application/json; charset=utf-8'):
        data=body.encode('utf-8')
        try:
            self.send_response(status)
            self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',CSP)
            self.send_header('Connection','close');self.end_headers();self.wfile.write(data)
            self._discard_rejected_body()
        except OSError: pass
        self.close_connection=True

    def _discard_rejected_body(self):
        # Closing a socket with a pending POST body can reset it on Windows,
        # discarding the error response. Send the response first, then consume
        # only a bounded, unambiguous body under the existing socket timeout.
        if self.command!='POST' or getattr(self,'_body_read',False): return
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length',[]))!=1: return
        try:
            length=int(self.headers.get('Content-Length',''))
            if 0<length<=MAX_BYTES:
                self._body_read=True
                self.rfile.read(length)
        except (OSError,ValueError): pass

    def _error(self,status,message):
        self._send(status,dump_json({'error':message}))

    def _host_ok(self):
        port=self.server.server_address[1]
        hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
        if self.headers.get('Host') not in hosts or len(self.headers.get_all('Host',[]))!=1:
            self._error(403,'この画面はローカルホスト専用です');return False
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://{host}' for host in hosts}:
            self._error(403,'異なるOriginからのアクセスは拒否されました');return False
        return True

    def _token_ok(self):
        token=self.headers.get('X-CRC-Token','')
        if not token.isascii() or not secrets.compare_digest(token,self.server.session_token):
            self._error(403,'セッショントークンが一致しません。画面を再読み込みしてください');return False
        return True

    def do_GET(self):
        if not self._host_ok(): return
        path=self.path.partition('?')[0]
        if path=='/':
            html=files('cleanroomcheck').joinpath('web','index.html').read_text(encoding='utf-8')
            self._send(200,html.replace('__SESSION_TOKEN__',self.server.session_token),'text/html; charset=utf-8')
        elif path in {'/assets/app.js','/assets/common.css'}:
            name=path.rsplit('/',1)[-1]
            mime='text/javascript' if name.endswith('.js') else 'text/css'
            self._send(200,files('cleanroomcheck').joinpath('web',name).read_text(encoding='utf-8'),mime+'; charset=utf-8')
        elif path=='/api/bootstrap':
            if not self._token_ok(): return
            self._send(200,dump_json({'fields':field_catalog(),'rules':RULES,'sources':load_sources(),
                                    'examples':{name:example(name) for name in TEMPLATES},
                                    'today':date.today().isoformat(),'demo_date':'2026-10-14'}))
        else: self._error(404,'指定されたページはありません')

    def do_POST(self):
        if not self._host_ok() or not self._token_ok(): return
        if self.path.partition('?')[0] not in {'/api/evaluate','/api/validate'}:
            self._error(404,'指定されたAPIはありません');return
        if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':
            self._error(415,'application/jsonのみ受け付けます');return
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length',[]))!=1:
            self._error(400,'Content-Lengthを1つ指定してください');return
        try: length=int(self.headers.get('Content-Length',''))
        except ValueError:
            self._error(400,'Content-Lengthが不正です');return
        if not 0<length<=MAX_BYTES:
            self._error(413,'入力は2MiB以下にしてください');return
        try:
            self._body_read=True
            raw=self.rfile.read(length)
            if len(raw)!=length: raise ModelError('本文の長さが一致しません')
            payload=parse_json(raw.decode('utf-8'))
            obj(payload,{'model','model_json','as_of','max_evidence_age_days'},set(),'request')
            if ('model' in payload)==('model_json' in payload):
                raise ModelError('modelとmodel_jsonのいずれか1つを指定してください')
            if 'model_json' in payload and not isinstance(payload['model_json'],str):
                raise ModelError('model_jsonはJSON文字列で指定してください')
            model=validate_model(parse_json(payload['model_json']) if 'model_json' in payload else payload['model'])
            if self.path.partition('?')[0]=='/api/validate':
                self._send(200,dump_json({'valid':True,'model':model}));return
            as_of=parse_date(payload['as_of']) if 'as_of' in payload else date.today()
            result=evaluate(model,as_of,payload.get('max_evidence_age_days',90))
            self._send(200,dump_json({'result':result,'html':render_html(result),
                                    'questions_csv':questions_csv(result),'verification_csv':verification_csv(result)}))
        except (ModelError,UnicodeError) as exc:
            self._error(400,str(exc))
        except (socket.timeout,TimeoutError):
            self._error(408,'入力の受信がタイムアウトしました')


def make_server(port: int = 0) -> LocalServer:
    if type(port) is not int or not 0<=port<=65535: raise ModelError('portは0〜65535の整数です')
    server=LocalServer(('127.0.0.1',port),Handler)
    server.session_token=secrets.token_urlsafe(32)
    return server


def serve(port: int = 8765,open_browser: bool = False) -> None:
    server=make_server(port);url=f'http://127.0.0.1:{server.server_address[1]}/'
    print('CleanRoomCheck local UI: '+url,flush=True)
    print('外部公開・リバースプロキシ配下での利用は未対応。終了: Ctrl+C。入力は自動保存されません。',flush=True)
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try: server.serve_forever()
    finally: server.server_close()
