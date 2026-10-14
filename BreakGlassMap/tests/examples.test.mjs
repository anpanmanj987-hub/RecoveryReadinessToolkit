import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseModel} from '../src/schema.mjs';
import {analyze} from '../src/engine.mjs';
for(const [file,expected]of [['identity-outage',{ready:0,blocked:2,unknown:1}],['independent-path',{ready:2,blocked:0,unknown:1}],['switch-trap',{ready:0,blocked:1,unknown:0}],['switch-prepared',{ready:1,blocked:0,unknown:0}],['empty',{ready:0,blocked:0,unknown:1}]]){
 test(`documented fixture ${file} has expected outcomes`,()=>{const m=parseModel(readFileSync(new URL(`../examples/${file}.json`,import.meta.url),'utf8'));assert.deepEqual(analyze(m,undefined,{asOf:'2026-10-13'}).summary,expected);});
}
