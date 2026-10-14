/** Strict, versioned input boundary shared by the browser and CLI. */
export const LIMITS = Object.freeze({bytes:1048576,nodes:250,routes:16,depth:12,refs:8000,scenarios:32});
export const CATEGORIES = Object.freeze(['identity','network','credential','document','people','system','other']);
export class ModelError extends Error {
  constructor(message,path='model') { super(`${path}: ${message}`);this.name='ModelError';this.path=path; }
}
const schemaFail = (path,message) => {throw new ModelError(message,path);};
function schemaObject(value,path) {
  if(!value || typeof value!=='object' || Array.isArray(value) || ![Object.prototype,null].includes(Object.getPrototypeOf(value))) schemaFail(path,'expected an object');
}
function schemaKeys(value,allowed,path) {
  schemaObject(value,path);
  for(const k of Object.keys(value))if(!allowed.includes(k))schemaFail(`${path}.${k}`,'unknown field');
}
function schemaText(value,path,max=160,required=true) {
  if(value===undefined&&!required)return '';
  if(typeof value!=='string'||value.length>max||(required&&!value.trim()))schemaFail(path,`expected ${required?'nonempty ':''}text, maximum ${max} characters`);
  if(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value))schemaFail(path,'control characters are not allowed');
  return value;
}
function schemaId(value,path) {
  if(typeof value!=='string'||!(/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/).test(value)||['constructor','prototype','__proto__'].includes(value))schemaFail(path,'invalid identifier: use 1–64 letters, numbers, dots, hyphens or underscores, starting with a letter or number');
  return value;
}
export function validDate(value) {
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
  const date=new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===value;
}
function schemaEvidence(value,path) {
  if(value===undefined)return {status:'not-tested'};
  schemaKeys(value,['status','checkedAt','reviewer','reference','scope','conditionHash','maxAgeDays','notes'],path);
  if(!['not-tested','passed','failed'].includes(value.status))schemaFail(`${path}.status`,'expected not-tested, passed or failed');
  const result={status:value.status};
  if(value.conditionHash!==undefined){
    if(typeof value.conditionHash!=='string'||!/^bgm1-[a-f0-9]{16}$/.test(value.conditionHash))schemaFail(`${path}.conditionHash`,'invalid condition hash');
    result.conditionHash=value.conditionHash;
  }
  if(value.checkedAt!==undefined&&!validDate(value.checkedAt))schemaFail(`${path}.checkedAt`,'invalid date');
  if(value.status!=='not-tested'&&!validDate(value.checkedAt))schemaFail(`${path}.checkedAt`,'a valid date is required');
  if(value.checkedAt!==undefined)result.checkedAt=value.checkedAt;
  for(const field of ['reviewer','reference','scope']) {
    const text=schemaText(value[field],`${path}.${field}`,field==='reference'?500:160,value.status!=='not-tested');
    if(text)result[field]=text;
  }
  if(value.notes!==undefined)result.notes=schemaText(value.notes,`${path}.notes`,1000,false);
  if(value.maxAgeDays!==undefined&&(!Number.isInteger(value.maxAgeDays)||value.maxAgeDays<1||value.maxAgeDays>3650))schemaFail(`${path}.maxAgeDays`,'expected integer 1–3650');
  result.maxAgeDays=value.maxAgeDays??90;
  return result;
}
function schemaExpression(expr,path,ids,budget,depth=0) {
  if(depth>LIMITS.depth)schemaFail(path,'expression depth limit exceeded');
  schemaKeys(expr,['ref','all','any'],path);
  const keys=Object.keys(expr);
  if(keys.length!==1)schemaFail(path,'expression must have exactly one operator (ref/all/any)');
  const op=keys[0];
  if(op==='ref') {
    const id=schemaId(expr.ref,`${path}.ref`);
    if(!ids.has(id))schemaFail(path,`unknown reference ${id}`);
    if(++budget.refs>LIMITS.refs)schemaFail(path,'reference limit exceeded');
    return {ref:id};
  }
  if(!Array.isArray(expr[op])||expr[op].length<1||expr[op].length>250)schemaFail(path,'operator needs a nonempty array of 1–250 expressions');
  return {[op]:expr[op].map((x,i)=>schemaExpression(x,`${path}.${op}[${i}]`,ids,budget,depth+1))};
}
export function validateScenario(value,ids,path='scenario') {
  schemaKeys(value,['id','name','description','unavailable','unknown'],path);
  const result={id:schemaId(value.id,`${path}.id`),name:schemaText(value.name,`${path}.name`),description:schemaText(value.description,`${path}.description`,2000,false)};
  for(const field of ['unavailable','unknown']) {
    const list=value[field]===undefined?[]:value[field];
    if(!Array.isArray(list)||list.length>LIMITS.nodes)schemaFail(`${path}.${field}`,'expected a bounded array');
    result[field]=list.map((id,i)=>{schemaId(id,`${path}.${field}[${i}]`);if(!ids.has(id))schemaFail(`${path}.${field}`,`unknown reference ${id}`);return id;});
    if(new Set(result[field]).size!==result[field].length)schemaFail(`${path}.${field}`,'duplicate identifier');
  }
  if(result.unavailable.some(id=>result.unknown.includes(id)))schemaFail(path,'overlap: a node cannot be both unavailable and unknown');
  return result;
}
export function validateModel(input) {
  let size;
  try {size=new TextEncoder().encode(JSON.stringify(input)).length;}catch {schemaFail('model','input must be JSON-serializable');}
  if(size>LIMITS.bytes)schemaFail('model','input exceeds 1 MiB limit');
  schemaKeys(input,['schemaVersion','name','description','nodes','scenarios'],'model');
  if(input.schemaVersion!==1)schemaFail('model.schemaVersion','unsupported schema version; expected 1');
  const result={schemaVersion:1,name:schemaText(input.name,'model.name'),description:schemaText(input.description,'model.description',4000,false),nodes:[],scenarios:[]};
  if(!Array.isArray(input.nodes)||!input.nodes.length||input.nodes.length>LIMITS.nodes)schemaFail('model.nodes',`expected 1–${LIMITS.nodes} nodes`);
  const ids=new Set();
  for(const [i,node]of input.nodes.entries()) {
    schemaObject(node,`nodes[${i}]`);schemaId(node.id,`nodes[${i}].id`);
    if(ids.has(node.id))schemaFail(`nodes[${i}].id`,'duplicate node identifier');ids.add(node.id);
  }
  const budget={refs:0};
  result.nodes=input.nodes.map((node,i)=>{
    const p=`nodes[${i}]`;
    schemaKeys(node,['id','label','kind','category','initial','routes','owner','systemId','notes','evidence'],p);
    if(!['resource','action','goal'].includes(node.kind))schemaFail(`${p}.kind`,'expected resource, action or goal');
    const normalized={id:node.id,label:schemaText(node.label,`${p}.label`,120),kind:node.kind,category:node.category===undefined?'other':node.category,owner:schemaText(node.owner,`${p}.owner`,160,false),systemId:schemaText(node.systemId,`${p}.systemId`,120,false),notes:schemaText(node.notes,`${p}.notes`,2000,false),evidence:schemaEvidence(node.evidence,`${p}.evidence`)};
    if(!CATEGORIES.includes(normalized.category))schemaFail(`${p}.category`,'unknown category');
    if(node.kind==='resource') {
      if(node.routes!==undefined)schemaFail(p,'resource cannot have routes; model restoration as a separate action');
      normalized.initial=node.initial===undefined?'unknown':node.initial;
      if(!['available','unavailable','unknown'].includes(normalized.initial))schemaFail(`${p}.initial`,'expected available, unavailable or unknown');
    }else {
      if(node.initial!==undefined)schemaFail(p,'derived action/goal cannot have initial state');
      const routes=node.routes===undefined?[]:node.routes;
      if(!Array.isArray(routes)||routes.length>LIMITS.routes)schemaFail(`${p}.routes`,`expected 0–${LIMITS.routes} routes`);
      const routeIds=new Set();
      normalized.routes=routes.map((route,j)=>{
        const rp=`${p}.routes[${j}]`;
        schemaKeys(route,['id','label','requires'],rp);schemaId(route.id,`${rp}.id`);
        if(routeIds.has(route.id))schemaFail(rp,'duplicate route identifier');routeIds.add(route.id);
        return {id:route.id,label:schemaText(route.label,`${rp}.label`,160),requires:schemaExpression(route.requires,`${rp}.requires`,ids,budget)};
      });
    }
    return normalized;
  });
  if(!result.nodes.some(n=>n.kind==='goal'))schemaFail('model.nodes','at least one goal is required');
  const scenarios=input.scenarios===undefined?[]:input.scenarios;
  if(!Array.isArray(scenarios)||scenarios.length>LIMITS.scenarios)schemaFail('model.scenarios',`expected 0–${LIMITS.scenarios} scenarios`);
  const scenarioIds=new Set();
  result.scenarios=scenarios.map((s,i)=>{
    const v=validateScenario(s,ids,`scenarios[${i}]`);
    if(scenarioIds.has(v.id))schemaFail(`scenarios[${i}].id`,'duplicate scenario identifier');scenarioIds.add(v.id);return v;
  });
  if(!result.scenarios.length)result.scenarios=[{id:'baseline',name:'Baseline',description:'',unavailable:[],unknown:[]}];
  return result;
}
export function parseModel(text) {
  if(typeof text!=='string')schemaFail('JSON','expected text');
  if(new TextEncoder().encode(text).length>LIMITS.bytes)schemaFail('JSON','input exceeds 1 MiB limit');
  let value;
  try {value=JSON.parse(text.replace(/^\uFEFF/,''));}catch {schemaFail('JSON','invalid JSON; check commas, quotation marks and brackets');}
  return validateModel(value);
}
