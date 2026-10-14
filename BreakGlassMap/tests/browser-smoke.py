"""Optional real-browser checks. Requires Python playwright and a local Chromium.
Run: python tests/browser-smoke.py --browser /usr/bin/chromium
No production dependencies; this is a development-only harness.
"""
import argparse, json, pathlib, tempfile, subprocess, atexit
from playwright.sync_api import sync_playwright, Error
parser=argparse.ArgumentParser()
parser.add_argument('--browser',default='/usr/bin/chromium')
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parent.parent
server=subprocess.Popen(['node','scripts/serve.mjs','--port','0'],cwd=root,stdout=subprocess.PIPE,text=True)
atexit.register(server.terminate)
base=server.stdout.readline().strip()
assert base.startswith('http://127.0.0.1:'),base
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.browser,headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[];network=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.on('request',lambda r: network.append(r.url) if r.url.startswith(('http:','https:')) and not r.url.startswith(base) else None)
    injected=False
    html=(root/'dist/BreakGlassMap.html').read_text(encoding='utf-8')
    def inject(target, saved=None):
        # Test-only storage double for opaque about:blank origins. Never part of app.
        target.evaluate('''values => {
          const store=new Map(Object.entries(values));
          Object.defineProperty(window,'localStorage',{value:{
            get length(){return store.size},key(i){return [...store.keys()][i]??null},
            getItem(k){return store.get(String(k))??null},
            setItem(k,v){store.set(String(k),String(v))},
            removeItem(k){store.delete(String(k))},clear(){store.clear()}
          }});
        }''',saved or {})
        target.set_content(html)
    try:
        page.goto(base)
    except Error as e:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(e):raise
        injected=True
        page.close();page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.on('request',lambda r: network.append(r.url) if r.url.startswith(('http:','https:')) else None)
        inject(page)
    page.get_by_role('heading',name='復旧の「はじめの一歩」を、確かめる。').wait_for()
    assert page.locator('[data-metric="blocked"]').inner_text()=='2'
    assert page.locator('[data-metric="unknown"]').inner_text()=='1'
    assert page.evaluate('localStorage.length')==0
    page.get_by_role('button',name='独立した復旧手段を試す').click()
    assert page.locator('[data-metric="ready"]').inner_text()=='2'
    assert page.locator('[data-metric="unknown"]').inner_text()=='1'
    assert page.get_by_text('変更前との比較',exact=True).is_visible()
    assert page.get_by_text('未訓練',exact=True).count()>0
    page.locator('#toast').wait_for(state='hidden')
    page.screenshot(path=str(root/'docs/screenshots/independent-path.png'),full_page=True)
    page.get_by_role('button',name='変更前に戻す').click()
    assert page.locator('[data-metric="blocked"]').inner_text()=='2'
    page.locator('#scenario-select').select_option('baseline')
    assert page.locator('[data-metric="blocked"]').inner_text()=='0'
    page.locator('#scenario-select').select_option('identity-outage')
    page.locator('#toast').wait_for(state='hidden')
    page.screenshot(path=str(root/'docs/screenshots/overview.png'),full_page=True)
    page.get_by_role('button',name='構成を編集',exact=False).click()
    page.get_by_role('button',name='条件を追加',exact=True).click()
    page.locator('#node-id').fill('test-condition')
    page.locator('#node-label').fill('テスト用条件')
    page.locator('#node-initial').select_option('unknown')
    page.get_by_role('button',name='変更を適用',exact=True).click()
    assert page.get_by_text('テスト用条件',exact=True).count()>0
    page.get_by_role('button',name='モデルJSON',exact=True).click()
    payload=json.loads(page.locator('#json-text').input_value())
    assert any(n['id']=='test-condition' for n in payload['nodes'])
    page.locator('#json-text').fill('{')
    page.get_by_role('button',name='JSONを適用',exact=True).click()
    assert page.locator('#json-dialog').is_visible()
    page.get_by_role('button',name='閉じる',exact=True).last.click()
    page.get_by_role('button',name='シナリオ分析',exact=False).click()
    assert page.locator('[data-metric="blocked"]').inner_text()=='2'
    page.get_by_role('button',name='JSON保存',exact=True).click()
    # Verify export in a separate expected-download check.
    with page.expect_download() as export:
        page.get_by_role('button',name='JSON保存',exact=True).click()
    with tempfile.TemporaryDirectory() as d:
        saved=pathlib.Path(d)/'model.json';export.value.save_as(saved)
        assert any(n['id']=='test-condition' for n in json.loads(saved.read_text(encoding='utf-8'))['nodes'])
    # Stored state is explicit and unencrypted. Do not change this without UX approval.
    page.locator('#persist-toggle').check()
    assert page.evaluate('localStorage.length')>0
    if injected:
        saved=page.evaluate('Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>localStorage.key(i)).map(k=>[k,localStorage.getItem(k)]))')
        page.close();page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.on('request',lambda r: network.append(r.url) if r.url.startswith(('http:','https:')) else None)
        inject(page,saved)
    else:
        page.reload()
    page.get_by_role('heading',name='復旧の「はじめの一歩」を、確かめる。').wait_for()
    page.locator('#persist-toggle').uncheck()
    assert page.evaluate('localStorage.length')==0
    # Record evidence, then change the same scenario's conditions: not current anymore.
    page.get_by_role('button',name='構成を編集',exact=False).click()
    page.locator('button[data-action="edit-node"][data-id="offline-runbook"]').click()
    page.locator('#node-initial').select_option('available')
    page.locator('#evidence-status').select_option('passed')
    page.locator('#evidence-date').fill('2026-10-12')
    page.locator('#evidence-reviewer').fill('Test reviewer')
    page.locator('#evidence-ref').fill('DRILL-TEST-01')
    page.locator('#evidence-bind').check()
    page.get_by_role('button',name='変更を適用',exact=True).click()
    page.get_by_role('button',name='シナリオ分析',exact=False).click()
    assert page.get_by_text('記録あり（本人申告）',exact=True).count()>0
    page.get_by_role('button',name='障害条件を編集',exact=True).click()
    page.locator('#override-maintenance-net').select_option('unavailable')
    page.get_by_role('button',name='シナリオを適用',exact=True).click()
    assert page.get_by_text('構成・障害条件が変更済み',exact=True).count()>0

    # AND/OR route editor and nested JSON must retain the exact condition semantics.
    page.get_by_role('button',name='構成を編集',exact=False).click()
    page.get_by_role('button',name='モデルJSON',exact=True).click()
    nested={'schemaVersion':1,'name':'Nested test','nodes':[
      {'id':'a','label':'Available condition','kind':'resource','initial':'available'},
      {'id':'b','label':'Unavailable condition','kind':'resource','initial':'unavailable'},
      {'id':'switch','label':'Nested operation','kind':'action','routes':[{'id':'main','label':'Nested','requires':{'all':[{'ref':'a'},{'any':[{'ref':'b'},{'ref':'a'}]}]}}]},
      {'id':'g','label':'Test goal','kind':'goal','routes':[{'id':'main','label':'Use operation','requires':{'ref':'switch'}}]}
    ]}
    page.locator('#json-text').fill(json.dumps(nested))
    page.get_by_role('button',name='JSONを適用',exact=True).click()
    page.locator('button[data-action="edit-node"][data-id="switch"]').click()
    assert json.loads(page.locator('[name="route-expr-0"]').input_value())==nested['nodes'][2]['routes'][0]['requires']
    page.locator('#node-owner').fill('Different owner')
    page.get_by_role('button',name='変更を適用',exact=True).click()
    page.get_by_role('button',name='モデルJSON',exact=True).click()
    saved=json.loads(page.locator('#json-text').input_value())
    assert next(n for n in saved['nodes'] if n['id']=='switch')['routes'][0]['requires']==nested['nodes'][2]['routes'][0]['requires']
    page.get_by_role('button',name='閉じる',exact=True).last.click()
    page.locator('button[data-action="edit-node"][data-id="g"]').click()
    page.get_by_role('button',name='経路を追加',exact=True).click()
    page.locator('[name="route-ref-1"][value="a"]').check()
    page.get_by_role('button',name='変更を適用',exact=True).click()
    page.get_by_role('button',name='モデルJSON',exact=True).click()
    saved=json.loads(page.locator('#json-text').input_value())
    assert len(next(n for n in saved['nodes'] if n['id']=='g')['routes'])==2
    page.get_by_role('button',name='閉じる',exact=True).last.click()
    page.locator('button[data-action="delete-node"][data-id="a"]').click()
    assert '参照されています' in page.locator('#toast').inner_text()

    # File import is transactional and labels are text, never HTML or code.
    hostile={'schemaVersion':1,'name':'Hostile text test','nodes':[
      {'id':'a','label':'<img src=x onerror="window.BGM_HACKED=1">','kind':'resource','initial':'unknown','owner':'=1+1'},
      {'id':'g','label':'Safe goal','kind':'goal','routes':[{'id':'main','label':'</script><script>window.BGM_HACKED=1</script>','requires':{'ref':'a'}}]}
    ]}
    page.once('dialog',lambda d:d.accept())
    page.locator('#import-file').set_input_files({'name':'hostile.json','mimeType':'application/json','buffer':json.dumps(hostile).encode()})
    page.get_by_role('heading',name='Hostile text test',exact=True).wait_for()
    assert page.locator('#app img').count()==0
    assert page.evaluate('window.BGM_HACKED === undefined')
    page.locator('#import-file').set_input_files({'name':'broken.json','mimeType':'application/json','buffer':b'{'})
    page.wait_for_function("document.querySelector('#toast').textContent.includes('読み込みを中止')")
    assert page.get_by_role('heading',name='Hostile text test',exact=True).is_visible()
    with page.expect_download() as csv_export:
        page.locator('details.menu').evaluate('(el)=>el.open=true')
        page.get_by_role('button',name='チェックリスト CSV',exact=True).click()
    with tempfile.TemporaryDirectory() as d:
        f=pathlib.Path(d)/'export.csv';csv_export.value.save_as(f)
        assert "'=1+1" in f.read_text(encoding='utf-8')
    page.once('dialog',lambda d:d.accept())
    page.get_by_role('button',name='架空デモを開く',exact=True).click()
    assert page.locator('[data-metric="blocked"]').inner_text()=='2'
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#toast').wait_for(state='hidden')
    page.screenshot(path=str(root/'docs/screenshots/mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
    assert not errors, errors
    assert not network, network
    # Storage unavailable must degrade gracefully rather than accuse the model of corruption.
    native=browser.new_page()
    native.set_content(html)
    assert native.locator('[data-metric="blocked"]').inner_text()=='2'
    assert native.locator('#persist-toggle').is_disabled()
    assert native.locator('#toast').is_hidden()
    native.close()
    mode='DOM injection + explicit test-only storage double (managed browser blocks ALL URL navigation)' if injected else 'local HTTP + native localStorage'
    print('MODE:',mode)
    print('PASS: scenarios; circular/independent paths; CRUD; nested AND/OR route preservation; referenced deletion guard; transactional hostile/invalid JSON file import; evidence revalidation after scenario edit; CSV export sanitization; opt-in persistence logic; storage-denied graceful fallback; mobile overflow; no page errors; no external HTTP(S) requests.')

    browser.close()
