import test from 'node:test';
import assert from 'node:assert/strict';
import {conditionFingerprint} from '../src/fingerprint.mjs';
import {analyze} from '../src/engine.mjs';
const m=()=>({schemaVersion:1,name:'x',nodes:[{id:'a',label:'a',kind:'resource',initial:'available'},{id:'g',label:'g',kind:'goal',routes:[{id:'main',label:'Main',requires:{ref:'a'}}]}],scenarios:[{id:'base',name:'Baseline',unavailable:[],unknown:[]}]});
function withEvidence(){const model=m();model.nodes[0].evidence={status:'passed',checkedAt:'2026-10-12',reviewer:'Reviewer',reference:'EXERCISE-1',scope:'base',conditionHash:conditionFingerprint(model,model.scenarios[0])};return model;}
test('fingerprint is stable and versioned',()=>assert.match(conditionFingerprint(m(),m().scenarios[0]),/^bgm1-[a-f0-9]{16}$/));
test('metadata and evidence changes do not change condition fingerprint',()=>{const model=m(),before=conditionFingerprint(model,model.scenarios[0]);model.name='renamed';model.nodes[0].owner='x';model.nodes[0].evidence={status:'not-tested'};assert.equal(conditionFingerprint(model,model.scenarios[0]),before);});
test('condition edits change fingerprint',()=>{const model=m(),before=conditionFingerprint(model,model.scenarios[0]);model.nodes[0].initial='unknown';assert.notEqual(conditionFingerprint(model,model.scenarios[0]),before);});
test('scenario edits change fingerprint even when id is retained',()=>{const model=m(),before=conditionFingerprint(model,model.scenarios[0]);model.scenarios[0].unavailable=['a'];assert.notEqual(conditionFingerprint(model,model.scenarios[0]),before);});
test('node array reordering does not change fingerprint',()=>{const model=m(),before=conditionFingerprint(model,model.scenarios[0]);model.nodes.reverse();assert.equal(conditionFingerprint(model,model.scenarios[0]),before);});
test('bound recent matching evidence is current',()=>assert.equal(analyze(withEvidence(),'base',{asOf:'2026-10-13'}).nodes.find(n=>n.id==='a').evidenceStatus,'current'));
test('condition edit does not silently revalidate evidence',()=>{const model=withEvidence();model.nodes[0].initial='unknown';assert.equal(analyze(model,'base',{asOf:'2026-10-13'}).nodes.find(n=>n.id==='a').evidenceStatus,'conditions-changed');});
test('unbound historical success is not current',()=>{const model=withEvidence();delete model.nodes[0].evidence.conditionHash;assert.equal(analyze(model,'base',{asOf:'2026-10-13'}).nodes.find(n=>n.id==='a').evidenceStatus,'unbound');});
