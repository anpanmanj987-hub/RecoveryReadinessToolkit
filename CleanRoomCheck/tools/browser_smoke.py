"""Real Chromium integration checks. Optional development dependency: playwright."""
from __future__ import annotations
import json
import os
import sys
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from cleanroomcheck.server import make_server

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]) if len(sys.argv)>1 else root/'output/browser'
out.mkdir(parents=True,exist_ok=True)
server=make_server(0);port=server.server_address[1]
thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True);thread.start()
results=[];errors=[];external=[]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1360,'height':1000},accept_downloads=True,locale='ja-JP')
        page=context.new_page();page.on('pageerror',lambda err:errors.append(str(err)))
        page.on('request',lambda req:external.append(req.url) if req.url.startswith(('http://','https://')) and not req.url.startswith(f'http://127.0.0.1:{port}/') else None)
        page.on('dialog',lambda dialog:dialog.accept())
        page.goto(f'http://127.0.0.1:{port}/');expect(page.locator('#editor')).to_be_visible()
        expect(page.locator('#projectName')).to_have_value('架空金融グループ / クリーン環境検討')
        page.screenshot(path=str(out/'ui-start.png'))
        results.append('UI bootstrap and packaged templates')
        page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
        expect(page.locator('.metric.failed .number')).to_have_text('35')
        expect(page.locator('.metric.unknown .number')).to_have_text('36')
        page.locator('#results').scroll_into_view_if_needed();page.wait_for_timeout(300);page.screenshot(path=str(out/'ui-risky.png'))
        results.append('Risky demo: 35 failed / 36 unknown / 13 passed / 12 not applicable')
        with page.expect_download() as pending:page.locator('#saveHtml').click()
        pending.value.save_as(str(out/'downloaded-report.html'))
        text=(out/'downloaded-report.html').read_text(encoding='utf-8')
        assert 'CRC-ID-001' in text and 'Content-Security-Policy' in text
        results.append('HTML export with findings and security policy')
        page.locator('#fact-dedicated_admin_device').select_option('true')
        expect(page.locator('#results')).to_be_hidden()
        page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
        expect(page.locator('.metric.failed .number')).to_have_text('32')
        results.append('Form edit invalidates previous report and changes evaluation')
        page.locator('#template').select_option('azure-improved');page.locator('#loadTemplate').click()
        page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
        expect(page.locator('.metric.failed .number')).to_have_text('0');expect(page.locator('.metric.unknown .number')).to_have_text('39')
        page.locator('#results').scroll_into_view_if_needed();page.wait_for_timeout(300);page.screenshot(path=str(out/'ui-improved.png'))
        results.append('Improved design: zero failed with 39 explicitly unresolved checks')
        page.locator('details.panel summary').click()
        text=page.locator('#rawModel').input_value().replace('"demo": true','"demo": true, "demo": false')
        page.locator('#rawModel').fill(text);expect(page.locator('#evaluate')).to_be_disabled()
        page.locator('#applyJson').click();expect(page.locator('#status')).to_contain_text('重複')
        page.locator('#discardJson').click();expect(page.locator('#evaluate')).to_be_enabled()
        results.append('Advanced JSON duplicate-key rejection and dirty-state guard')
        page.locator('#proof-independent_identity').fill('say');page.locator('#proof-independent_identity').dispatch_event('change')
        page.locator('#evaluate').click();expect(page.locator('#results')).to_be_visible()
        expect(page.locator('.metric.unknown .number')).to_have_text('42')
        results.append('Self-reported evidence cannot produce a positive result')
        def delayed(route):
            response=route.fetch()
            page.evaluate("document.getElementById('projectName').value='入力変更の競合テスト';document.getElementById('projectName').dispatchEvent(new Event('change'))")
            route.fulfill(response=response)
        page.route('**/api/evaluate',delayed)
        page.locator('#evaluate').click();expect(page.locator('#status')).to_contain_text('入力が変更されたため')
        expect(page.locator('#results')).to_be_hidden();page.unroute('**/api/evaluate',delayed)
        results.append('In-flight input changes discard stale evaluation responses')
        report=context.new_page();report.on('pageerror',lambda err:errors.append(str(err)))
        report.goto((out/'downloaded-report.html').resolve().as_uri())
        report.locator('[data-filter="FAILED"]').click();expect(report.locator('.finding:visible')).to_have_count(35)
        report.locator('#expand').click();expect(report.locator('.finding[open]')).to_have_count(96)
        report.screenshot(path=str(out/'report-top.png'))
        results.append('Standalone report filtering and evidence expansion')
        mobile=context.new_page();mobile.set_viewport_size({'width':390,'height':844});mobile.goto(f'http://127.0.0.1:{port}/')
        expect(mobile.locator('#editor')).to_be_visible()
        width=mobile.evaluate('document.documentElement.scrollWidth');assert width<=392,width
        mobile.screenshot(path=str(out/'ui-mobile.png'))
        results.append('390px mobile layout without page-wide overflow')
        assert not errors,errors;assert not external,external
        results.append('No browser JavaScript errors and no external network requests')
        browser.close()
finally:
    server.shutdown();server.server_close();thread.join(timeout=3)
report={'checks_passed':len(results),'checks':results,'javascript_errors':errors,'external_requests':external}
(out/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
