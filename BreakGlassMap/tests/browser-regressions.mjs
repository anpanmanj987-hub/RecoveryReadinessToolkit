/** Optional real-browser regressions. Install Playwright separately, then run:
 * node tests/browser-regressions.mjs [--browser PATH_TO_CHROMIUM]
 * PLAYWRIGHT_MODULE may point to a separately installed Playwright directory.
 */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {conditionFingerprint} from '../src/fingerprint.mjs';

const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
const args=process.argv.slice(2);
if(args.length&&!(args.length===2&&args[0]==='--browser'))throw new Error('Usage: node tests/browser-regressions.mjs [--browser PATH]');
const root=fileURLToPath(new URL('..',import.meta.url));
const server=spawn(process.execPath,['scripts/serve.mjs','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
let browser;
try{
  const base=await new Promise((resolve,reject)=>{
    let output='';const timer=setTimeout(()=>reject(new Error('Server did not start')),5000);
    server.on('error',error=>{clearTimeout(timer);reject(error);});
    server.on('exit',()=>{clearTimeout(timer);reject(new Error('Server exited before startup'));});
    server.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);resolve(output.trim());}});
  });
  browser=await chromium.launch({headless:true,...(args[1]?{executablePath:args[1]}:{})});
  const page=await browser.newPage();const errors=[];const external=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(/^https?:/.test(request.url())&&!request.url().startsWith(base+'/'))external.push(request.url());});
  async function applyModel(model){
    await page.goto(base);
    await page.getByRole('button',{name:'構成を編集',exact:false}).click();
    await page.getByRole('button',{name:'モデルJSON',exact:true}).click();
    await page.locator('#json-text').fill(JSON.stringify(model));
    await page.getByRole('button',{name:'JSONを適用',exact:true}).click();
  }
  async function readModel(){
    await page.getByRole('button',{name:'モデルJSON',exact:true}).click();
    const value=JSON.parse(await page.locator('#json-text').inputValue());
    await page.getByRole('button',{name:'閉じる',exact:true}).last().click();return value;
  }
  async function readAnalysis(){
    await page.locator('details.menu').evaluate(el=>{el.open=true;});
    const pending=page.waitForEvent('download');
    await page.getByRole('button',{name:'分析結果 JSON',exact:true}).click();
    const download=await pending;const stream=await download.createReadStream();let text='';
    for await(const chunk of stream)text+=chunk.toString();return JSON.parse(text);
  }
  const fixture=expr=>{
    const model={schemaVersion:1,name:'No-op route edit',nodes:[
      {id:'a',label:'Condition A',kind:'resource',initial:'available'},
      {id:'b',label:'Condition B',kind:'resource',initial:'available'},
      {id:'g',label:'Recovery goal',kind:'goal',routes:[{id:'main',label:'Main',requires:expr}]}
    ],scenarios:[{id:'baseline',name:'Baseline',unavailable:[],unknown:[]}]};
    model.nodes[2].evidence={status:'passed',checkedAt:'2026-10-12',reviewer:'Reviewer',reference:'TEST-1',scope:'baseline',maxAgeDays:3650,conditionHash:conditionFingerprint(model,model.scenarios[0])};
    return model;
  };
  for(const expr of [{ref:'a'},{all:[{ref:'b'},{ref:'a'}]},{all:[{ref:'a'},{ref:'a'}]}]){
    const model=fixture(expr);await applyModel(model);
    await page.locator('button[data-action="edit-node"][data-id="g"]').click();
    await page.locator('#node-owner').fill('Updated owner');
    await page.getByRole('button',{name:'変更を適用',exact:true}).click();
    assert.deepEqual((await readModel()).nodes.find(n=>n.id==='g').routes[0].requires,expr,'A metadata edit must preserve the exact stored condition');
    assert.equal((await readAnalysis()).nodes.find(n=>n.id==='g').evidenceStatus,'current','A metadata edit must retain current bound evidence');
  }
  // Changing a dependency must still change the fingerprint and require review.
  await applyModel(fixture({ref:'a'}));
  await page.locator('button[data-action="edit-node"][data-id="g"]').click();
  await page.locator('[name="route-ref-0"][value="b"]').check();
  await page.getByRole('button',{name:'変更を適用',exact:true}).click();
  assert.deepEqual((await readModel()).nodes.find(n=>n.id==='g').routes[0].requires,{all:[{ref:'a'},{ref:'b'}]});
  assert.equal((await readAnalysis()).nodes.find(n=>n.id==='g').evidenceStatus,'conditions-changed');
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('PASS: metadata edits preserve ref/conjunction order/duplicate conditions and bound evidence; dependency edits invalidate evidence; native local HTTP; no page errors or external requests.');
}finally{
  if(browser)await browser.close();server.kill();if(server.exitCode===null)await once(server,'exit');
}
