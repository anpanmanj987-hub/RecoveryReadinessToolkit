import test from 'node:test';
import assert from 'node:assert/strict';
import {parseModel,validateModel,ModelError} from '../src/schema.mjs';

const model=()=>({schemaVersion:1,name:'Input boundary',nodes:[
  {id:'resource',label:'Initial condition',kind:'resource',initial:'available'},
  {id:'goal',label:'Recovery goal',kind:'goal',routes:[{id:'main',label:'Main',requires:{ref:'resource'}}]}
],scenarios:[{id:'baseline',name:'Baseline',unavailable:[],unknown:[]}]});

// Explicit null is malformed JSON model data, rather than an omitted field.
// Treating null arrays as empty can silently discard outage conditions/routes.
for(const {name,path,edit} of [
  {name:'resource initial',path:'nodes[0].initial',edit:m=>{m.nodes[0].initial=null;}},
  {name:'node category',path:'nodes[0].category',edit:m=>{m.nodes[0].category=null;}},
  {name:'derived routes',path:'nodes[1].routes',edit:m=>{m.nodes[1].routes=null;}},
  {name:'scenario array',path:'model.scenarios',edit:m=>{m.scenarios=null;}},
  {name:'unavailable overrides',path:'scenarios[0].unavailable',edit:m=>{m.scenarios[0].unavailable=null;}},
  {name:'unknown overrides',path:'scenarios[0].unknown',edit:m=>{m.scenarios[0].unknown=null;}}
])test(`rejects explicit null ${name} at the input boundary`,()=>{
  const input=model();edit(input);
  assert.throws(()=>parseModel(JSON.stringify(input)),error=>error instanceof ModelError&&error.path===path);
});

test('omitted optional state and arrays retain documented defaults',()=>{
  const input=model();delete input.nodes[0].initial;delete input.nodes[1].routes;delete input.scenarios;
  const normalized=validateModel(input);
  assert.equal(normalized.nodes[0].initial,'unknown');
  assert.equal(normalized.nodes[0].category,'other');
  assert.deepEqual(normalized.nodes[1].routes,[]);
  assert.deepEqual(normalized.scenarios,[{id:'baseline',name:'Baseline',description:'',unavailable:[],unknown:[]}]);
});
