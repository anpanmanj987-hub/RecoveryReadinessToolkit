import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,mkdirSync,writeFileSync,rmSync,readdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const root=new URL('..',import.meta.url);
const html=()=>readFileSync(new URL('dist/BreakGlassMap.html',root),'utf8');
test('standalone script and stylesheet match CSP hashes',()=>{const text=html();for(const tag of ['style','script']){const code=text.match(new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`))[1];const hash=createHash('sha256').update(code).digest('base64');assert.ok(text.includes(`'sha256-${hash}'`));if(tag==='script')assert.doesNotThrow(()=>new vm.Script(code));}assert.ok(text.includes("connect-src 'none'"));assert.ok(!text.includes('__SCRIPT__'));});
test('standalone document does not depend on remote scripts, links, fonts or images',()=>{const text=html();assert.ok(!/<script[^>]+src\s*=/i.test(text));assert.ok(!/<link[^>]+href\s*=/i.test(text));assert.ok(!/@import\s/.test(text));});
test('build is byte-identical with LF and Windows CRLF checkouts',()=>{
 const dir=mkdtempSync(join(tmpdir(),'bgm-build-'));
 try{
  for(const folder of ['src','web','scripts']){
   mkdirSync(join(dir,folder),{recursive:true});
   for(const filename of readdirSync(new URL(folder+'/',root))){
    if(!/\.(mjs|html|css)$/.test(filename))continue;
    const text=readFileSync(new URL(folder+'/'+filename,root),'utf8');writeFileSync(join(dir,folder,filename),text.replace(/\r?\n/g,'\r\n'));
   }
  }
  const r=spawnSync(process.execPath,['scripts/build.mjs'],{cwd:dir,encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  assert.equal(readFileSync(join(dir,'dist/BreakGlassMap.html'),'utf8'),html());
 }finally{rmSync(dir,{recursive:true,force:true});}
});
