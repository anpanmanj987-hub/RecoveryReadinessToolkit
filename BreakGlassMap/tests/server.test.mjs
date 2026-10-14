import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from '../scripts/serve.mjs';
import http from 'node:http';
import {fileURLToPath} from 'node:url';
const server=createServer();
let base;
test.before(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));base=`http://127.0.0.1:${server.address().port}`;});
test.after(async()=>{await new Promise(r=>server.close(r));});
test('loopback server serves standalone app',async()=>{const r=await fetch(base);assert.equal(r.status,200);assert.match(await r.text(),/BreakGlassMap/);assert.equal(r.headers.get('cache-control'),'no-store');});
test('server never exposes repository or arbitrary paths',async()=>{for(const path of ['/package.json','/src/schema.mjs','/.git/config','/etc/passwd'])assert.equal((await fetch(base+path)).status,404);});
test('server rejects mutation methods',async()=>assert.equal((await fetch(base,{method:'POST',body:'x'})).status,405));
test('server rejects hostile Host header (DNS rebinding defense)',async()=>{const status=await new Promise((resolve,reject)=>{const req=http.get(base,{headers:{Host:'hostile.example'}},res=>{res.resume();resolve(res.statusCode)});req.on('error',reject);});assert.equal(status,403);});

test('malformed request target returns 400 without crashing the server', async (t) => {
  const {spawn} = await import('node:child_process');
  const child=spawn(process.execPath,[fileURLToPath(new URL('../scripts/serve.mjs',import.meta.url)),'--port','0'],{stdio:['ignore','pipe','pipe']});
  t.after(()=>child.kill());
  // Use a child so a pre-fix uncaught parser error becomes an assertion failure,
  // rather than aborting this test process or masking the connection reset.
  const url=await new Promise((resolve,reject)=>{
    let output='';
    const timer=setTimeout(()=>reject(new Error('server did not start')),3000);
    child.on('error',e=>{clearTimeout(timer);reject(e);});
    child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);resolve(output.trim());}});
    child.on('exit',()=>{clearTimeout(timer);reject(new Error('server exited before startup'));});
  });
  const address=new URL(url);
  for(const target of ['//[','http://[']){
    const status=await new Promise(resolve=>{
      const req=http.get({hostname:address.hostname,port:address.port,path:target},res=>{res.resume();resolve(res.statusCode);});
      req.on('error',()=>resolve('connection-reset'));
      req.setTimeout(3000,()=>req.destroy());
    });
    assert.equal(status,400);
    assert.equal((await fetch(url)).status,200);
  }
});
