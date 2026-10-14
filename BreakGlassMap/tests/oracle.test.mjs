import test from 'node:test';
import assert from 'node:assert/strict';
import {analyze} from '../src/engine.mjs';
import {validateModel} from '../src/schema.mjs';
// Independent oracle: enumerate every Boolean fixed point, then intersect all of
// them (the least fixed point of a monotone Boolean system). No iterative closure.
function oracle(model,scenario,optimistic){
 const nodes=model.nodes,index=new Map(nodes.map((n,i)=>[n.id,i]));
 const expr=(e,mask)=>e.ref!==undefined?Boolean(mask&(1<<index.get(e.ref))):e.all?e.all.every(x=>expr(x,mask)):e.any.some(x=>expr(x,mask));
 let intersection=(1<<nodes.length)-1,count=0;
 for(let mask=0;mask<(1<<nodes.length);mask++){
  const matches=nodes.every((n,i)=>{
   let expected;
   if(scenario.unavailable.includes(n.id))expected=false;
   else if(scenario.unknown.includes(n.id))expected=optimistic;
   else if(n.kind==='resource')expected=n.initial==='available'||optimistic&&n.initial==='unknown';
   else expected=!n.routes.length?optimistic:n.routes.some(r=>expr(r.requires,mask));
   return Boolean(mask&(1<<i))===Boolean(expected);
  });
  if(matches){intersection&=mask;count++;}
 }
 assert.ok(count>0,'a monotone system must have a fixed point');
 return nodes.map((_,i)=>Boolean(intersection&(1<<i)));
}
test('500 generated models match exhaustive fixed-point oracle under both uncertainty bounds',()=>{
 let seed=0x1d942b7;const rnd=n=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)%n;};
 for(let example=0;example<500;example++){
  const ids=Array.from({length:7},(_,i)=>'n'+i);
  const expression=(depth=0)=>depth>=2||rnd(3)===0?{ref:ids[rnd(ids.length)]}:{[rnd(2)?'all':'any']:Array.from({length:1+rnd(3)},()=>expression(depth+1))};
  const nodes=ids.map((id,i)=>i<3?{id,label:id,kind:'resource',initial:['available','unavailable','unknown'][rnd(3)]}:{id,label:id,kind:i===6?'goal':'action',routes:Array.from({length:rnd(3)},(_,j)=>({id:'r'+j,label:'r'+j,requires:expression()}))});
  const scenario={id:'test',name:'Test',unavailable:ids.filter(()=>rnd(9)===0),unknown:[]};scenario.unknown=ids.filter(id=>!scenario.unavailable.includes(id)&&rnd(9)===0);
  const m=validateModel({schemaVersion:1,name:'Generated',nodes,scenarios:[scenario]});
  const lo=oracle(m,scenario,false),hi=oracle(m,scenario,true),actual=analyze(m,'test',{asOf:'2026-10-13'});
  nodes.forEach((n,i)=>assert.equal(actual.nodes.find(r=>r.id===n.id).status,lo[i]?'ready':hi[i]?'unknown':'blocked',`example ${example}, ${n.id}`));
 }
});
test('as-of impossible date is rejected',()=>assert.throws(()=>analyze({schemaVersion:1,name:'x',nodes:[{id:'g',label:'g',kind:'goal',routes:[]}]},undefined,{asOf:'2026-02-30'}),/date/));
test('model over 250 nodes is rejected',()=>assert.throws(()=>validateModel({schemaVersion:1,name:'x',nodes:[...Array.from({length:250},(_,i)=>({id:'r'+i,label:'r',kind:'resource'})),{id:'g',label:'g',kind:'goal'}]}),/250/));
test('expression depth over 12 is rejected',()=>{let e={ref:'r'};for(let i=0;i<13;i++)e={all:[e]};assert.throws(()=>validateModel({schemaVersion:1,name:'x',nodes:[{id:'r',label:'r',kind:'resource'},{id:'g',label:'g',kind:'goal',routes:[{id:'r',label:'r',requires:e}]}]}),/depth/);});
test('resource reference budget rejects 8001 occurrences',()=>{const routes=Array.from({length:16},(_,i)=>({id:'r'+i,label:'r',requires:{all:Array.from({length:250},()=>({ref:'r'}))}}));assert.throws(()=>validateModel({schemaVersion:1,name:'x',nodes:[{id:'r',label:'r',kind:'resource'},{id:'a',label:'a',kind:'action',routes},{id:'b',label:'b',kind:'action',routes},{id:'g',label:'g',kind:'goal',routes:[{id:'r',label:'r',requires:{ref:'a'}}]}]}),/reference limit/);});
