import {conditionFingerprint} from './fingerprint.mjs';
import {validateModel,validateScenario,validDate,ModelError} from './schema.mjs';

/** Nodes are capabilities, not observed live services. `ready` is model feasibility only. */
export const STATUS_LABELS = Object.freeze({ready:'構成上成立',blocked:'開始不可',unknown:'情報不足'});
export const EVIDENCE_LABELS = Object.freeze({'not-tested':'未訓練',current:'記録あり（本人申告）',stale:'確認期限超過',failed:'訓練失敗',future:'未来日付','scope-mismatch':'別シナリオの記録',unbound:'構成との紐付けなし','conditions-changed':'構成・障害条件が変更済み'});
export function listRefs(expr) {
  if(expr.ref!==undefined)return [expr.ref];
  return [...new Set((expr.all??expr.any).flatMap(listRefs))];
}
function engineBoolean(expr,set) {
  if(expr.ref!==undefined)return set.has(expr.ref);
  if(expr.all)return expr.all.every(x=>engineBoolean(x,set));
  return expr.any.some(x=>engineBoolean(x,set));
}
function engineWitness(expr,set) {
  if(expr.ref!==undefined)return [expr.ref];
  if(expr.all)return [...new Set(expr.all.flatMap(x=>engineWitness(x,set)))];
  return engineWitness(expr.any.find(x=>engineBoolean(x,set)),set);
}
function engineClosure(nodes,scenario,optimistic) {
  const blocked=new Set(scenario.unavailable),unknown=new Set(scenario.unknown),known=new Set(),proof=new Map();
  for(const n of nodes) {
    if(blocked.has(n.id))continue;
    if(unknown.has(n.id)) {if(optimistic){known.add(n.id);proof.set(n.id,{stage:0,routeId:null,dependencies:[],basis:'scenario-unknown'});}continue;}
    const seed=n.kind==='resource'?(n.initial==='available'||(optimistic&&n.initial==='unknown')):(optimistic&&!n.routes.length);
    if(seed){known.add(n.id);proof.set(n.id,{stage:0,routeId:null,dependencies:[],basis:n.kind==='resource'?n.initial:'undefined-routes'});}
  }
  for(let round=1;round<=nodes.length;round++) {
    const additions=[];
    for(const n of nodes) {
      if(n.kind==='resource'||known.has(n.id)||blocked.has(n.id)||unknown.has(n.id))continue;
      const route=n.routes.find(r=>engineBoolean(r.requires,known));
      if(route)additions.push({id:n.id,stage:round,routeId:route.id,dependencies:engineWitness(route.requires,known),basis:'route'});
    }
    if(!additions.length)break;
    for(const {id,...w}of additions){known.add(id);proof.set(id,w);}
  }
  return {known,proof};
}
function engineScc(nodes) {
  const byId=new Map(nodes.map(n=>[n.id,n]));let index=0;
  const stack=[],onStack=new Set(),indices=new Map(),low=new Map(),components=[];
  const edges=id=>(byId.get(id).routes??[]).flatMap(r=>listRefs(r.requires));
  function visit(id) {
    indices.set(id,index);low.set(id,index++);stack.push(id);onStack.add(id);
    for(const dep of edges(id)) {
      if(!indices.has(dep)){visit(dep);low.set(id,Math.min(low.get(id),low.get(dep)));}
      else if(onStack.has(dep))low.set(id,Math.min(low.get(id),indices.get(dep)));
    }
    if(low.get(id)===indices.get(id)) {
      const part=[];let last;
      do {last=stack.pop();onStack.delete(last);part.push(last);}while(last!==id);
      if(part.length>1||edges(id).includes(id))components.push(part.sort());
    }
  }
  nodes.forEach(n=>{if(!indices.has(n.id))visit(n.id);});
  return components.sort((a,b)=>a[0].localeCompare(b[0],'en'));
}
export function evidenceState(evidence,asOf,scenarioId,fingerprint) {
  if(!evidence||evidence.status==='not-tested')return 'not-tested';
  const days=(new Date(`${asOf}T00:00:00Z`)-new Date(`${evidence.checkedAt}T00:00:00Z`))/86400000;
  if(days<0)return 'future';
  if(evidence.status==='failed')return 'failed';
  if(evidence.scope!==scenarioId)return 'scope-mismatch';
  if(days>(evidence.maxAgeDays??90))return 'stale';
  if(!evidence.conditionHash)return 'unbound';
  if(evidence.conditionHash!==fingerprint)return 'conditions-changed';
  return 'current';
}
/** Deterministic under an explicit asOf YYYY-MM-DD. No network, storage or model mutation. */
export function analyze(input,scenarioArg,options={}) {
  const model=validateModel(input),nodes=[...model.nodes].sort((a,b)=>a.id.localeCompare(b.id,'en'));
  const asOf=options.asOf??new Date().toISOString().slice(0,10);
  if(!validDate(asOf))throw new ModelError('invalid as-of date','analysis');
  const selected=typeof scenarioArg==='object'&&scenarioArg!==null?scenarioArg:model.scenarios.find(s=>s.id===(scenarioArg??model.scenarios[0].id));
  if(!selected)throw new ModelError('unknown scenario','analysis');
  const scenario=validateScenario(selected,new Set(nodes.map(n=>n.id)));
  const conditionHash=conditionFingerprint(model,scenario);
  const lower=engineClosure(nodes,scenario,false),upper=engineClosure(nodes,scenario,true);
  const state=id=>lower.known.has(id)?'ready':upper.known.has(id)?'unknown':'blocked';
  const expressionState=expr=>engineBoolean(expr,lower.known)?'ready':engineBoolean(expr,upper.known)?'unknown':'blocked';
  const results=nodes.map(n=>({id:n.id,label:n.label,kind:n.kind,category:n.category,owner:n.owner,systemId:n.systemId,status:state(n.id),stage:lower.proof.get(n.id)?.stage??null,witness:lower.proof.get(n.id)??null,possibleWitness:upper.proof.get(n.id)??null,evidenceStatus:evidenceState(n.evidence,asOf,scenario.id,conditionHash),forced:scenario.unavailable.includes(n.id)?'unavailable':scenario.unknown.includes(n.id)?'unknown':null,routes:(n.routes??[]).map(r=>({id:r.id,label:r.label,status:expressionState(r.requires),dependencies:listRefs(r.requires).map(id=>({id,status:state(id)}))}))}));
  const byId=new Map(nodes.map(n=>[n.id,n])),resultById=new Map(results.map(n=>[n.id,n]));
  // Walk only unresolved branches that can explain the result. For unknown ORs,
  // impossible branches are not causal; ready alternatives never become blockers.
  function unresolved(expr) {
    const es=expressionState(expr);if(es==='ready')return [];
    if(expr.ref!==undefined)return [expr.ref];
    const children=expr.all??expr.any;
    const relevant=expr.all?(es==='blocked'?children.filter(x=>expressionState(x)==='blocked'):children.filter(x=>expressionState(x)==='unknown')):(es==='unknown'?children.filter(x=>expressionState(x)==='unknown'):children);
    return [...new Set(relevant.flatMap(unresolved))];
  }
  const traces=new Map();
  const goals=results.filter(n=>n.kind==='goal');
  for(const g of goals) {
    const visited=new Set(),leaves=[];
    function walk(id) {
      if(visited.has(id)||state(id)==='ready')return;visited.add(id);
      const n=byId.get(id),r=resultById.get(id);
      if(r.forced||n.kind==='resource'||!n.routes.length){leaves.push(id);return;}
      for(const route of n.routes) {
        if(r.status==='unknown'&&expressionState(route.requires)==='blocked')continue;
        unresolved(route.requires).forEach(walk);
      }
    }
    walk(g.id);traces.set(g.id,{visited,leaves:leaves.sort()});
    g.blockers=leaves.sort();g.unresolvedDependencies=[...visited].filter(id=>id!==g.id).sort();
  }
  const cycles=engineScc(nodes).map((part,i)=>({id:`cycle-${i+1}`,nodes:part,status:part.every(id=>state(id)==='ready')?'resolved':part.some(id=>state(id)==='unknown')?'unknown':'blocked',affectedGoals:goals.filter(g=>g.status!=='ready'&&part.some(id=>traces.get(g.id).visited.has(id))).map(g=>g.id)}));
  const checklist=[];
  for(const n of nodes) {
    const r=resultById.get(n.id),affected=goals.filter(g=>traces.get(g.id).leaves.includes(n.id)).map(g=>g.id);
    if(affected.length)checklist.push({id:`availability:${n.id}`,nodeId:n.id,label:n.label,code:r.status==='unknown'?'confirm-condition':'design-alternative',priority:r.status==='unknown'?'P2':'P1',status:r.status,owner:n.owner,systemId:n.systemId,affectedGoals:affected,question:r.status==='unknown'?(n.kind!=='resource'&&!n.routes.length?'開始に必要な条件・復旧経路を定義してください。':'障害時にこの条件が成立するか、担当者と確認してください。'):'この条件を必要としない独立した代替手段、または明示的な復旧操作を設計してください。',evidence:n.evidence});
    if(r.evidenceStatus!=='current')checklist.push({id:`evidence:${n.id}`,nodeId:n.id,label:n.label,code:`evidence-${r.evidenceStatus}`,priority:r.evidenceStatus==='failed'?'P1':'P3',status:r.evidenceStatus,owner:n.owner,systemId:n.systemId,affectedGoals:[],question:r.evidenceStatus==='failed'?'訓練失敗と構成上の条件を照合し、原因と再試験結果を記録してください。':`選択したシナリオでの確認範囲・担当者・日付・証跡参照を記録してください（${EVIDENCE_LABELS[r.evidenceStatus]}）。`,evidence:n.evidence});
  }
  for(const c of cycles.filter(x=>x.affectedGoals.length))checklist.push({id:c.id,nodeId:c.nodes[0],label:'循環する復旧条件',code:'review-cycle',priority:'P1',status:c.status,owner:'',systemId:'',affectedGoals:c.affectedGoals,question:`${c.nodes.map(id=>byId.get(id).label).join(' / ')}：循環の外から開始できる独立条件を確認してください。構造上の循環のみで障害原因を確定しないでください。`,evidence:{status:'not-tested'}});
  checklist.sort((a,b)=>a.priority.localeCompare(b.priority)||a.id.localeCompare(b.id,'en'));
  const summary={ready:0,blocked:0,unknown:0};goals.forEach(g=>summary[g.status]++);
  return {schemaVersion:1,toolVersion:'0.1.0-alpha.1',modelName:model.name,asOf,scenario,conditionHash,summary,nodes:results,goals,cycles,checklist,limitations:['入力された条件に基づく構成上の判定であり、実際の復旧成功・安全性・RTO達成を保証しません。','強制停止した条件はシナリオ中は利用できません。回復させる操作・独立経路は別ノードで明示してください。','訓練記録は利用者の申告です。証跡の内容や真正性、全体の訓練完了を検証しません。']};
}
