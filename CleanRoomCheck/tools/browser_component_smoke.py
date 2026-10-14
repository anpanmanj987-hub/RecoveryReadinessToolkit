"""Offline Chromium component tests, without navigation or browser network access.
The test injects local HTML/CSS/JS and an in-memory fetch adapter to the same
Python engine. HTTP security is tested separately in tests/test_server.py.
This is NOT a native-browser HTTP end-to-end or actual-download test.
"""
from pathlib import Path
from datetime import date
import json
import os
import sys
from playwright.sync_api import sync_playwright, expect
from cleanroomcheck.catalog import RULES, field_catalog, load_sources
from cleanroomcheck.cli import TEMPLATES, example
from cleanroomcheck.engine import evaluate
from cleanroomcheck.io import parse_json
from cleanroomcheck.model import validate_model, parse_date
from cleanroomcheck.report import render_html, questions_csv, verification_csv

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]) if len(sys.argv)>1 else root/'output/browser-components'
out.mkdir(parents=True,exist_ok=True)
bootstrap={'fields':field_catalog(),'rules':RULES,'sources':load_sources(),'examples':{n:example(n) for n in TEMPLATES},'today':'2026-10-14','demo_date':'2026-10-14'}
html=(root/'cleanroomcheck/web/index.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="/assets/common.css">','').replace('<script defer src="/assets/app.js"></script>','')
css=(root/'cleanroomcheck/web/common.css').read_text(encoding='utf-8');js=(root/'cleanroomcheck/web/app.js').read_text(encoding='utf-8')

def adapter(source,path,body):
    try:
        if path=='/api/bootstrap': return {'ok':True,'data':bootstrap}
        model=validate_model(parse_json(body['model_json']) if 'model_json' in body else body['model'])
        if path=='/api/validate': return {'ok':True,'data':{'valid':True,'model':model}}
        result=evaluate(model,parse_date(body.get('as_of','2026-10-14')),body.get('max_evidence_age_days',90))
        return {'ok':True,'data':{'result':result,'html':render_html(result),'questions_csv':questions_csv(result),'verification_csv':verification_csv(result)}}
    except Exception as exc: return {'ok':False,'data':{'error':str(exc)}}

shim="""window.delayEvaluation=false; window.downloadedBlobs=[];
window.fetch=async(path,options)=>{const body=options?.body?JSON.parse(options.body):null;const answer=await window.localTestAPI(path,body);if(path==='/api/evaluate'&&window.delayEvaluation)await new Promise(resolve=>setTimeout(resolve,250));return {ok:answer.ok,json:async()=>answer.data};};
URL.createObjectURL=blob=>{window.downloadedBlobs.push(blob);return 'blob:component-test-only';};URL.revokeObjectURL=()=>{};HTMLAnchorElement.prototype.click=function(){};
"""
checks=[];errors=[];requests=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1360,'height':1000},locale='ja-JP')
    def mount(page):
        page.on('pageerror',lambda err:errors.append(str(err)));page.on('request',lambda req:requests.append(req.url));page.on('dialog',lambda dialog:dialog.accept())
        page.expose_binding('localTestAPI',adapter);page.set_content(html);page.add_style_tag(content=css);page.evaluate(shim);page.add_script_tag(content=js);expect(page.locator('#editor')).to_be_visible()
    page=context.new_page();mount(page)
    page.screenshot(path=str(out/'ui-start.png'));checks.append('Offline component bootstrap and packaged templates')
    page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
    expect(page.locator('.metric.failed .number')).to_have_text('35');expect(page.locator('.metric.unknown .number')).to_have_text('36')
    page.locator('#results').scroll_into_view_if_needed();page.wait_for_timeout(300);page.screenshot(path=str(out/'ui-risky.png'))
    checks.append('Risky demo renders 35 failed and 36 unknown')
    page.locator('#saveHtml').click();blob=page.evaluate('window.downloadedBlobs[0].text()');assert 'CRC-ID-001' in blob
    (out/'component-export.html').write_text(blob,encoding='utf-8');checks.append('HTML Blob generation (native download intentionally not exercised)')
    page.locator('#fact-dedicated_admin_device').select_option('true');expect(page.locator('#results')).to_be_hidden()
    page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible();expect(page.locator('.metric.failed .number')).to_have_text('32')
    checks.append('Form edit invalidates old results and recomputes')
    page.locator('#template').select_option('azure-improved');page.locator('#loadTemplate').click();page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
    expect(page.locator('.metric.failed .number')).to_have_text('0');expect(page.locator('.metric.unknown .number')).to_have_text('39')
    page.locator('#results').scroll_into_view_if_needed();page.wait_for_timeout(300);page.screenshot(path=str(out/'ui-improved.png'));checks.append('Improved design keeps 39 unresolved checks visible')
    page.locator('details.panel summary').click();text=page.locator('#rawModel').input_value().replace('"demo": true','"demo": true, "demo": false')
    page.locator('#rawModel').fill(text);expect(page.locator('#evaluate')).to_be_disabled();page.locator('#applyJson').click();expect(page.locator('#status')).to_contain_text('重複');page.locator('#discardJson').click();expect(page.locator('#evaluate')).to_be_enabled()
    checks.append('Advanced JSON duplicate-key and dirty-state guards')
    page.locator('#proof-independent_identity').fill('say');page.locator('#proof-independent_identity').dispatch_event('change');page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible();expect(page.locator('.metric.unknown .number')).to_have_text('42')
    checks.append('Self-reported evidence cannot yield a positive result')
    page.evaluate('window.delayEvaluation=true');page.locator('#evaluate').click();page.locator('#projectName').fill('競合テスト');page.locator('#projectName').dispatch_event('change');expect(page.locator('#status')).to_contain_text('入力が変更されたため');expect(page.locator('#results')).to_be_hidden()
    checks.append('Stale in-flight evaluation responses discarded')
    report=context.new_page();report.on('pageerror',lambda err:errors.append(str(err)));report.set_content(blob);report.locator('[data-filter="FAILED"]').click();expect(report.locator('.finding:visible')).to_have_count(35);report.locator('#expand').click();expect(report.locator('.finding[open]')).to_have_count(96);report.screenshot(path=str(out/'report-top.png'))
    checks.append('Standalone report inline-script CSP, filters and expansion')
    mobile=context.new_page();mobile.set_viewport_size({'width':390,'height':844});mount(mobile);width=mobile.evaluate('document.documentElement.scrollWidth');assert width<=392,width;mobile.screenshot(path=str(out/'ui-mobile.png'))
    checks.append('Responsive 390px layout without page-wide overflow')
    assert not errors,errors;assert not requests,requests
    checks.append('No JavaScript errors or browser network requests in component harness')
    browser.close()
summary={'mode':'offline DOM component test with local Python engine adapter; not native HTTP E2E','checks_passed':len(checks),'checks':checks,'javascript_errors':errors,'browser_network_requests':requests}
(out/'browser-component-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
