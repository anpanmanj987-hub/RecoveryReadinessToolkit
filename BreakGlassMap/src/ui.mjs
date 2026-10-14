import {conditionFingerprint} from './fingerprint.mjs';
import {validateModel,parseModel,validDate,CATEGORIES,LIMITS} from './schema.mjs';
import {analyze,listRefs,STATUS_LABELS,EVIDENCE_LABELS} from './engine.mjs';
import {escapeHtml,toCsv,toHtml} from './report.mjs';
import {DEMO,improvedDemo,emptyModel} from './demo.mjs';

const h=escapeHtml;
const $=selector=>document.querySelector(selector);
const CATEGORY_LABELS={identity:'認証',network:'ネットワーク',credential:'資格情報の取得条件',document:'手順・文書',people:'人・承認',system:'システム',other:'その他'};
const KIND_LABELS={resource:'初期条件',action:'操作・能力',goal:'復旧目標'};
const INITIAL_LABELS={available:'利用可能（申告）',unavailable:'利用不可',unknown:'未確認'};
const STORAGE_KEY='breakglassmap.workspace.v1';
const OPTIN_KEY='breakglassmap.persistence.v1';
const ICON_PATHS={shield:'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Zm-1 5-2 5h4l-2 5',map:'M4 5h6v5H4zM14 14h6v5h-6zM14 4h6v5h-6zM7 10v6h7M10 7h4',check:'m5 12 4 4L19 6',lock:'M6 10h12v11H6zM8 10V7a4 4 0 0 1 8 0v3M12 14v3',question:'M9 8a3 3 0 1 1 5 2c-2 1-2 2-2 3M12 17h.01',arrow:'M4 12h15m-6-6 6 6-6 6',download:'M12 3v12m-5-5 5 5 5-5M5 17v4h14v-4',upload:'M12 16V4m-5 5 5-5 5 5M5 17v4h14v-4',plus:'M12 5v14M5 12h14',edit:'m14 5 5 5M4 20l4-1L20 7l-4-4L4 15v5Z',close:'m6 6 12 12M6 18 18 6',file:'M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6M9 16h6',globe:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM3 12h18M12 3c-5 5-5 13 0 18 5-5 5-13 0-18',undo:'M9 6 4 11l5 5M4 11h10a5 5 0 0 1 5 5',settings:'M4 7h16M8 4v6M4 17h16M16 14v6',list:'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01',book:'M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3V4Zm9 2v15',trash:'M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7'};
function icon(name,size=16){return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${ICON_PATHS[name]??ICON_PATHS.file}"></path></svg>`;}
function badge(status,label){return `<span class="badge ${h(status)}">${h(label??STATUS_LABELS[status]??EVIDENCE_LABELS[status]??status)}</span>`;}
function button(action,label,ico='',cls='',data=''){return `<button type="button" class="button ${cls}" data-action="${action}" ${data}>${ico?icon(ico):''}${h(label)}</button>`;}
const uiState={model:validateModel(structuredClone(DEMO)),scenarioId:'identity-outage',custom:null,asOf:new Date().toISOString().slice(0,10),tab:'overview',selected:'goal-identity',filter:'all',search:'',persist:false,storageAvailable:true,dirty:false,comparison:null};
let analysis,editingNode=null,editingScenario=null,toastTimer;
function toast(message,error=false){clearTimeout(toastTimer);const el=$('#toast');el.textContent=message;el.hidden=false;el.className=error?'error':'';toastTimer=setTimeout(()=>{el.hidden=true;},error?11000:4500);}
function restoreStored(){
  try {
    let optedIn;
    try{optedIn=localStorage.getItem(OPTIN_KEY)==='yes';}catch{uiState.storageAvailable=false;return;}
    if(!optedIn)return;
    uiState.persist=true;
    const raw=localStorage.getItem(STORAGE_KEY);if(!raw)return;
    if(new TextEncoder().encode(raw).length>LIMITS.bytes+4096)throw new Error('保存内容が上限を超えています。');
    const saved=JSON.parse(raw);
    const m=validateModel(saved.model);
    uiState.model=m;uiState.scenarioId=m.scenarios.some(s=>s.id===saved.scenarioId)?saved.scenarioId:m.scenarios[0].id;
    uiState.selected=m.nodes.find(n=>n.kind==='goal').id;
    if(validDate(saved.asOf))uiState.asOf=saved.asOf;
  }catch(error){uiState.persist=false;toast(`保存データを読み込めませんでした。デモを表示します。${error.message}`,true);}
}
function persist(){
  if(!uiState.persist)return;
  try{localStorage.setItem(OPTIN_KEY,'yes');localStorage.setItem(STORAGE_KEY,JSON.stringify({version:1,model:uiState.model,scenarioId:uiState.scenarioId,asOf:uiState.asOf}));}
  catch{uiState.persist=false;try{localStorage.removeItem(OPTIN_KEY);localStorage.removeItem(STORAGE_KEY);}catch{}toast('保存できませんでした。メモリ上の変更は残っています。JSON保存をご利用ください。',true);}
}
function commitModel(candidate,{resetScenario=false,keepComparison=false}={}){
  const next=validateModel(candidate); // Transaction boundary: never partially replace a valid model.
  uiState.model=next;uiState.dirty=true;
  if(resetScenario||!next.scenarios.some(s=>s.id===uiState.scenarioId))uiState.scenarioId=next.scenarios[0].id;
  uiState.custom=null;
  if(!next.nodes.some(n=>n.id===uiState.selected))uiState.selected=next.nodes.find(n=>n.kind==='goal').id;
  if(!keepComparison)uiState.comparison=null;
  persist();render();
}
function currentScenario(){return uiState.custom??uiState.scenarioId;}
function render(){
  analysis=analyze(uiState.model,currentScenario(),{asOf:uiState.asOf});
  const tabs=[['overview','シナリオ分析','map'],['model','構成を編集','edit'],['checklist','確認・訓練票','list'],['guide','使い方','book']];
  $('#app').innerHTML=`<div class="shell"><aside class="sidebar"><div><div class="brand"><span class="brand-mark">${icon('shield',26)}</span><span>BreakGlassMap<div class="brand-sub">RECOVERY READINESS</div></span></div></div><div><p class="workspace-label">WORKSPACE</p><nav aria-label="メインメニュー">${tabs.map(([tab,label,ico],i)=>`<button class="nav-item ${uiState.tab===tab?'active':''}" data-action="tab" data-tab="${tab}" ${uiState.tab===tab?'aria-current="page"':''}>${icon(ico,17)}<span>${h(label)}</span><span class="nav-num">0${i+1}</span></button>`).join('')}</nav></div><div class="sidebar-note">${icon('lock',18)}<strong>構成情報は、この端末に。</strong>外部通信・LLM呼び出しなし。資格情報の秘密値は入力しないでください。<br><br>図が成立しても、実機訓練の代わりにはなりません。</div><div class="sidebar-footer"><span>OPEN SOURCE · MIT</span><span>α 0.1.0</span></div></aside><main class="main"><header class="topbar"><div class="breadcrumb">WORKSPACE <span aria-hidden="true">/</span> RECOVERY READINESS</div><div class="top-actions"><span class="pill">LOCAL ONLY</span>${button('import','JSONを開く','upload')}${button('export-model','JSON保存','download')}<details class="menu"><summary class="button">${icon('file')}レポート</summary><div class="menu-options">${button('export-html','HTMLレポート','file','ghost')}${button('export-csv','チェックリスト CSV','list','ghost')}${button('export-result','分析結果 JSON','download','ghost')}</div></details></div></header>${uiState.tab==='overview'?overview():uiState.tab==='model'?modelView():uiState.tab==='checklist'?checklistView():guideView()}<footer class="footnote"><div class="disclaimer">${icon('shield',13)} 構成上の開始可否を点検する机上分析です。実際の復旧成功・安全性・RTO達成は保証しません。訓練記録は別に確認してください。</div><div class="privacy"><label><input id="persist-toggle" type="checkbox" ${uiState.persist?'checked':''} ${!uiState.storageAvailable?'disabled':''}>このブラウザに保存する</label><span>${!uiState.storageAvailable?'この環境では保存不可':uiState.persist?'有効（未暗号化）':'無効・メモリ上のみ'}${uiState.dirty?' / 変更あり':''}</span></div></footer></main></div>`;
}
function pageHead(eyebrow,title,copy){return `<section class="page-head"><div><p class="eyebrow">${h(eyebrow)}</p><h1>${h(title)}</h1><p class="subcopy">${h(copy)}</p></div><div class="head-note"><strong>${h(uiState.model.name)}</strong>${uiState.model.nodes.length}条件・操作 / ${analysis.goals.length}復旧目標<br>${uiState.persist?'ブラウザ保存 有効':'外部送信なし・自動保存なし'}</div></section>`;}
function overview(){
  const canTry=['offline-kit','offline-runbook'].every(id=>uiState.model.nodes.some(n=>n.id===id&&n.kind==='resource'))&&!uiState.comparison;
  const s=analysis.summary;
  const insightTitle=s.blocked?'復旧手順があっても、その操作を始められない条件があります。':s.unknown?'開始経路は見えてきました。残る未確認条件を確かめましょう。':'入力された条件では、すべての復旧目標に開始経路があります。';
  return `${pageHead('TABLETOP EXERCISE','復旧の「はじめの一歩」を、確かめる。','認証・PAM・手順書が止まったとき。必要な操作を、どこから始められるかを点検します。')}<section class="panel scenario-bar"><div class="field scenario-field"><label for="scenario-select">01 / 想定する障害</label><select id="scenario-select">${uiState.model.scenarios.map(s=>`<option value="${h(s.id)}" ${s.id===uiState.scenarioId?'selected':''}>${h(s.name)}</option>`).join('')}</select></div><div class="field date-field"><label for="as-of">訓練記録の評価基準日</label><input id="as-of" type="date" value="${uiState.asOf}"></div><div class="scenario-description">${h(analysis.scenario.description||'停止条件はシナリオ全体で継続する前提です。')}</div>${button('edit-scenario','障害条件を編集','settings')}</section><section class="metrics" aria-label="復旧目標の判定">${[['ready','構成上成立','入力条件上の開始経路あり','check'],['blocked','開始不可','必要条件が成立しない','lock'],['unknown','情報不足','条件・経路の追加確認が必要','question']].map(([status,label,note,ico])=>`<article class="panel metric ${status}"><div><div class="metric-label">${h(label)}</div><div class="metric-value" data-metric="${status}">${s[status]}</div><div class="metric-note">${h(note)}</div></div><div class="metric-icon">${icon(ico,24)}</div></article>`).join('')}</section><section class="panel insight"><div><div class="insight-title">${h(insightTitle)}</div><p>${uiState.model.name.startsWith('架空例')?'架空デモ：復旧用資格情報はPAM内、オンライン手順書は認証基盤に依存しています。':'初期条件・代替経路・切り替え操作の前提を、担当者と確認してください。'}</p></div>${canTry?button('whatif','独立した復旧手段を試す','arrow','primary'):button('tab','確認事項を見る','arrow','', 'data-tab="checklist"')}</section>${comparisonHtml()}<section class="analysis-grid"><article class="panel"><header class="panel-heading"><div><h2>復旧条件マップ</h2><p>条件・操作をクリックすると、依存関係と根拠を確認できます。</p></div><div class="legend"><span><i class="dot ready"></i>成立</span><span><i class="dot blocked"></i>不可</span><span><i class="dot unknown"></i>不明</span></div></header><div class="graph-wrap">${graphHtml()}</div><div class="graph-note">矢印：必要な条件 → 依存する操作。代替経路・AND/ORの正確な条件は詳細欄を参照。</div></article><div class="stack"><article class="panel"><header class="panel-heading"><h2>復旧目標</h2><span class="pill-neutral">${analysis.goals.length} GOALS</span></header><div class="goals">${analysis.goals.map(g=>`<button class="goal-card ${uiState.selected===g.id?'selected':''}" data-action="select-node" data-id="${g.id}"><div class="goal-top"><span class="goal-name">${h(g.label)}</span>${badge(g.status)}</div><div class="goal-meta"><span>${h(g.owner||'担当未設定')}</span><span>${h(EVIDENCE_LABELS[g.evidenceStatus])}</span></div></button>`).join('')}</div></article><article class="panel">${inspectorHtml()}</article></div></section>`;
}
function comparisonHtml(){
  if(!uiState.comparison)return '';
  const before=uiState.comparison.before.summary,after=analysis.summary;
  return `<section class="comparison"><strong>変更前との比較</strong><span>構成上成立 ${before.ready} → ${after.ready}</span><span>開始不可 ${before.blocked} → ${after.blocked}</span><span>情報不足 ${before.unknown} → ${after.unknown}</span><span>※代替手段の利用を仮定。訓練記録は変更していません。</span>${button('undo-whatif','変更前に戻す','undo','small')}</section>`;
}
function graphHtml(){
  let nodes=uiState.model.nodes;
  let truncation='';
  if(nodes.length>70){const preferred=new Set([uiState.selected,...analysis.goals.map(n=>n.id)]);nodes=[...nodes.filter(n=>preferred.has(n.id)),...nodes.filter(n=>!preferred.has(n.id))].slice(0,70);truncation='<p class="dependency-limit">表示は70要素まで。全件の分析は構成一覧とレポートで確認できます。</p>';}
  const groups=['resource','action','goal'].map(kind=>nodes.filter(n=>n.kind===kind));
  const height=Math.max(410,Math.max(...groups.map(g=>g.length))*68+78);
  const pos=new Map();groups.forEach((group,col)=>group.forEach((n,i)=>pos.set(n.id,{x:20+col*268,y:58+(group.length===1?(height-130)/2:i*(height-130)/Math.max(1,group.length-1))})));
  const rmap=new Map(analysis.nodes.map(n=>[n.id,n]));
  const paths=[];
  for(const node of nodes)for(const route of node.routes??[])for(const dep of listRefs(route.requires)){
    if(!pos.has(dep))continue;const a=pos.get(dep),b=pos.get(node.id);
    const ax=a.x+221,ay=a.y+25,bx=b.x,by=b.y+25;
    const path=a.x===b.x?`M${ax} ${ay} C${ax+27} ${ay},${ax+27} ${by},${ax} ${by}`:`M${ax} ${ay} C${ax+42} ${ay},${bx-42} ${by},${bx} ${by}`;
    paths.push(`<path d="${path}" class="graph-edge ${rmap.get(dep).status==='blocked'?'is-blocked':''}" marker-end="url(#edge-arrow)"><title>${h(dep)} → ${h(node.id)} / ${h(route.label)}</title></path>`);
  }
  return `${truncation}<svg class="graph" viewBox="0 0 805 ${height}" role="group" aria-label="復旧条件の依存関係図"><defs><marker id="edge-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#9aafa0"/></marker></defs>${['01 / CONDITIONS','02 / OPERATIONS','03 / GOALS'].map((s,i)=>`<text x="${20+i*268}" y="30" class="graph-lane">${s}</text>`).join('')}${paths.join('')}${nodes.map(n=>{const p=pos.get(n.id),r=rmap.get(n.id);const text=n.label.length>18?n.label.slice(0,17)+'…':n.label;return `<g class="graph-node ${uiState.selected===n.id?'selected':''}" data-action="select-node" data-id="${n.id}" role="button" tabindex="0" aria-label="${h(n.label)}：${h(STATUS_LABELS[r.status])}"><title>${h(n.label)} / ${h(STATUS_LABELS[r.status])}</title><rect x="${p.x}" y="${p.y}" width="221" height="50" rx="7"/><circle cx="${p.x+14}" cy="${p.y+18}" r="3" class="node-state ${r.status}"/><text x="${p.x+26}" y="${p.y+22}" class="node-title">${h(text)}</text><text x="${p.x+26}" y="${p.y+38}" class="node-meta">${h(KIND_LABELS[n.kind])} · ${h(n.id.length>25?n.id.slice(0,24)+'…':n.id)}</text></g>`;}).join('')}</svg>`;
}
function expressionHtml(expr,depth=0){
  if(depth>8)return '<span class="help-text">深い式はモデルJSONで確認してください。</span>';
  if(expr.ref!==undefined){const n=analysis.nodes.find(n=>n.id===expr.ref);return `<button class="dep" data-action="select-node" data-id="${h(expr.ref)}"><i class="dot ${n.status}"></i><span>${h(n.label)}</span></button>`;}
  return `<ul class="expr"><li><span class="operator">${expr.all?'AND / すべて必要':'OR / いずれかが必要'}</span></li>${(expr.all??expr.any).map(x=>`<li>${expressionHtml(x,depth+1)}</li>`).join('')}</ul>`;
}
function inspectorHtml(){
  const node=uiState.model.nodes.find(n=>n.id===uiState.selected)??uiState.model.nodes.find(n=>n.kind==='goal');
  const result=analysis.nodes.find(n=>n.id===node.id);
  const cycles=analysis.cycles.filter(c=>c.affectedGoals.includes(node.id)||c.nodes.includes(node.id)&&c.affectedGoals.length);
  return `<div class="inspector"><p class="eyebrow">SELECTED CONDITION</p><div class="inspector-title"><h3>${h(node.label)}</h3>${badge(result.status)}</div><div class="metadata">${h(node.id)} · ${h(KIND_LABELS[node.kind])}<br>担当：${h(node.owner||'未設定')} / ${h(node.systemId||'SYSID未設定')}<br>訓練記録：${badge(result.evidenceStatus)} ${node.evidence.checkedAt?h(node.evidence.checkedAt):''}</div>${result.forced?`<div class="wide-note">このシナリオで${result.forced==='unavailable'?'強制停止':'状態不明'}に設定されています。ほかの経路より優先されます。</div>`:''}${node.notes?`<p class="help-text">${h(node.notes)}</p>`:''}${node.kind==='resource'?`<div class="empty-note">初期条件：${h(INITIAL_LABELS[node.initial])}<br>利用可能は入力上の申告であり、実機の確認結果ではありません。</div>`:node.routes.length?`<p class="help-text">${node.routes.length}経路のうち、いずれかが成立すれば実行可能。</p>${node.routes.map(route=>{const r=result.routes.find(x=>x.id===route.id);return `<div class="route-card"><div class="route-title"><span>${h(route.label)}</span>${badge(r.status)}</div>${expressionHtml(route.requires)}</div>`;}).join('')}`:'<div class="empty-note">開始条件・復旧経路が未定義です。自動的に成立とは扱いません。</div>'}${cycles.length?`<div class="cycle-note">循環する条件が未解決目標に関係しています。循環の外から開始できる代替手段を確認してください。</div>`:''}<div class="section-line">${button('edit-node','条件・担当・証跡を編集','edit','small',`data-id="${node.id}"`)}</div></div>`;
}
function modelView(){
  return `${pageHead('MODEL WORKSPACE','復旧に必要な条件を、つなぐ。','初期条件 → 操作・能力 → 復旧目標。経路内はAND、経路間はORとして入力できます。')}<section class="panel model-info"><div><h2>${h(uiState.model.name)}</h2><p>${h(uiState.model.description||'モデルJSONから名称・説明を編集できます。')}</p></div>${button('edit-json','モデルJSON','file')}</section><div class="toolbar"><div class="group">${button('add-node','条件を追加','plus','primary','data-kind="resource"')}${button('add-node','操作を追加','plus','','data-kind="action"')}${button('add-node','目標を追加','plus','','data-kind="goal"')}</div><div class="group">${button('new-model','新規モデル','file')}${button('load-demo','架空デモを開く','map')}${button('new-scenario','シナリオ追加','plus')}</div></div><section class="panel table-wrap"><table class="data-table"><thead><tr><th>条件・操作</th><th>種類</th><th>担当 / SYSID</th><th>入力条件</th><th>現在の判定</th><th>編集</th></tr></thead><tbody>${uiState.model.nodes.map(n=>{const r=analysis.nodes.find(x=>x.id===n.id);return `<tr><td><div class="label">${h(n.label)}</div><small>${h(n.id)}</small></td><td>${h(KIND_LABELS[n.kind])}<small>${h(CATEGORY_LABELS[n.category])}</small></td><td>${h(n.owner||'未設定')}<small>${h(n.systemId||'—')}</small></td><td>${n.kind==='resource'?h(INITIAL_LABELS[n.initial]):`${n.routes.length}経路`}</td><td>${badge(r.status)}</td><td class="action-cell">${button('edit-node','編集','edit','small',`data-id="${n.id}"`)} ${button('delete-node','削除','trash','small ghost',`data-id="${n.id}"`)}</td></tr>`;}).join('')}</tbody></table></section><p class="row-count">${uiState.model.nodes.length} / ${LIMITS.nodes}要素。参照中の要素は先に経路の参照を解除してください。最終の復旧目標は削除できません。</p>`;
}
function checklistView(){
  const items=analysis.checklist.filter(i=>(uiState.filter==='all'||i.priority===uiState.filter)&&(!uiState.search||[i.label,i.owner,i.systemId,i.question].join(' ').toLowerCase().includes(uiState.search.toLowerCase())));
  return `${pageHead('ACTION & EVIDENCE','「確認したつもり」を、残さない。','構成上の詰まりと、訓練記録の不足を分けて整理します。証跡ファイルではなく参照番号・所在のみを記録してください。')}<div class="wide-note">P1：代替手段・循環・訓練失敗の見直し。P2：条件の確認。P3：訓練記録の追加・更新。優先度は作業の種類であり、事業影響のスコアではありません。</div><div class="toolbar"><div class="filter">${['all','P1','P2','P3'].map(f=>button('filter',f==='all'?'すべて':f,'',`small ${f===uiState.filter?'active':''}`,`data-filter="${f}"`)).join('')}</div><div class="group"><input class="table-search" id="check-search" type="search" placeholder="対象・担当・SYSIDで検索" aria-label="確認事項を検索" value="${h(uiState.search)}">${button('export-csv','CSVを書き出す','download')}${button('export-html','HTMLレポート','file')}</div></div><section class="panel table-wrap">${items.length?`<table class="data-table"><thead><tr><th>優先度</th><th>対象 / 担当</th><th>確認事項</th><th>証跡参照</th><th>記録</th></tr></thead><tbody>${items.map(i=>`<tr><td>${badge(i.priority==='P1'?'blocked':i.priority==='P2'?'unknown':'not-tested',i.priority)}</td><td><div class="label">${h(i.label)}</div><small>${h(i.owner||'担当未設定')} / ${h(i.systemId||'SYSID未設定')}</small></td><td>${h(i.question)}<small>${h(i.code)}</small></td><td>${h(i.evidence.reference||'—')}<small>${h(i.evidence.checkedAt||'未記録')}</small></td><td>${button('edit-node','記録','edit','small',`data-id="${i.nodeId}"`)}</td></tr>`).join('')}</tbody></table>`:'<div class="empty-state">この条件に一致する確認事項はありません。入力の網羅性や実際の復旧成功を保証するものではありません。</div>'}</section><p class="row-count">${items.length}件を表示 / 全${analysis.checklist.length}件。CSVは現在のフィルターによらず全件を書き出します。</p>`;
}
function guideView(){
  return `${pageHead('START HERE','障害時の「入口」から、考える。','BreakGlassMapは、復旧を実行するツールではありません。必要条件と独立した開始経路を、担当者と点検するためのOSSです。')}<div class="guide-grid"><section class="panel guide-card"><span class="guide-number">01 / FIRST RUN</span><h2>まずは架空デモで比較</h2><p>「認証基盤停止」を選ぶと、通常認証・PAM・資格情報・オンライン手順書が循環し、2つの目標が開始不可になります。</p><p>「独立した復旧手段を試す」で緊急認証手段とオフライン手順書を利用可能と仮定すると、2つの目標が構成上成立します。連絡先は未確認のままです。</p>${button('load-demo','架空デモを開く','arrow','primary')}</section><section class="panel guide-card"><span class="guide-number">02 / MODEL YOUR RECOVERY</span><h2>一つの復旧目標から登録</h2><p>「何にログインするか」「必要な回線・端末・資格情報の取得条件は何か」「手順書を読めるか」「承認者と連絡できるか」を登録します。</p><p><strong>初期条件</strong>は独立して利用可能かを申告します。依存関係のあるものは<strong>操作・能力</strong>にし、必要条件を経路として追加してください。</p>${button('new-model','新規モデルで始める','plus')}</section><section class="panel guide-card"><span class="guide-number">03 / READ THE RESULTS</span><h2>3つの判定と、別軸の訓練記録</h2><p>${badge('ready')} 入力された既知の条件から開始経路が成立。実機確認済みという意味ではありません。</p><p>${badge('unknown')} 未確認の初期条件、または未定義の経路が必要です。</p><p>${badge('blocked')} 不明条件を成立すると仮定しても、開始経路が見つかりません。</p><p>成功・失敗・日付・確認者・証跡参照・シナリオ範囲を別に記録します。構成と指定シナリオに紐付けた記録は、条件変更時に再確認が必要になります。保存した参照先や記録の真正性は検証しません。</p></section><section class="panel guide-card"><span class="guide-number">04 / MODEL LIMITS</span><h2>停止条件と復旧操作を混同しない</h2><p>シナリオの「強制停止」は、その条件が分析中ずっと失われる前提です。回復させる場合は、復旧操作とその後の利用能力を別ノードにして経路を明示します。</p><p>複数経路はOR、各経路内の必要条件はAND。JSONでは入れ子の<code>all</code> / <code>any</code> / <code>ref</code>も利用できます。</p><p>時間・順序制約・作業の競合・RTO・費用・実システムの状態は扱いません。表示する段階は論理上の依存順序です。</p></section><section class="panel guide-card"><span class="guide-number">05 / LOCAL & PRIVATE</span><h2>外部送信なし、保存は明示的に</h2><p>このHTMLだけで動作します。サーバー、LLM、外部API、CDNは不要です。既定はメモリ上のみ。再読み込み前にJSON保存してください。</p><p>ブラウザ保存と書き出しファイルは未暗号化です。パスワード・秘密鍵・トークンは入力せず、実際の構成情報も承認された場所に保管してください。</p><p>会社のブラウザ制約でHTMLを直接開けない場合、ソース一式の<code>npm start</code>でループバックのローカルHTTPを利用できます。</p></section><section class="panel guide-card"><span class="guide-number">06 / CLI & OPEN SOURCE</span><h2>レビュー・CIでも同じエンジン</h2><p>ソース一式にはCLI、JSONモデル例、スキーマ、テスト、英語・日本語READMEが含まれます。Node.js 22以上でパッケージの追加インストールなしに利用できます。</p><p><code>node bin/breakglassmap.mjs analyze examples/identity-outage.json --scenario identity-outage</code></p><p>出口コードは、入力エラー1、開始不可2、情報不足3、証跡ゲート4。<code>--fail-on none</code>でレポートのみ生成できます。</p><p>MIT License · v0.1.0-alpha.1。製品・クラウドの実仕様を自動検証するものではありません。</p></section></div>`;
}

function openNode(id,kind='resource'){
  const existing=uiState.model.nodes.find(n=>n.id===id);
  editingNode={originalId:existing?.id??null,draft:existing?structuredClone(existing):{id:`${kind}-${Date.now().toString(36)}`,label:'',kind,category:'other',owner:'',systemId:'',notes:'',evidence:{status:'not-tested',scope:uiState.scenarioId,maxAgeDays:90},...(kind==='resource'?{initial:'unknown'}:{routes:[]})}};
  renderNodeDialog();$('#node-dialog').showModal();
}
function flatRefs(expr){if(expr.ref!==undefined)return [expr.ref];if(expr.all?.every(x=>x.ref!==undefined))return expr.all.map(x=>x.ref);return null;}
function renderNodeDialog(){
  const n=editingNode.draft,e=n.evidence??{status:'not-tested'},d=$('#node-dialog');
  d.innerHTML=`<form id="node-form"><header class="dialog-header"><div><p class="eyebrow">${editingNode.originalId?'EDIT CONDITION':'ADD CONDITION'}</p><h2 id="node-dialog-title">${h(KIND_LABELS[n.kind])}を${editingNode.originalId?'編集':'追加'}</h2></div>${button('close-dialog','閉じる','close','ghost','data-dialog="node-dialog"')}</header><div class="dialog-body"><div class="form-grid"><div class="field"><label for="node-id">ID（英数字・ハイフン等）</label><input id="node-id" name="id" value="${h(n.id)}" ${editingNode.originalId?'readonly':''} maxlength="64" required></div><div class="field"><label for="node-label">表示名</label><input id="node-label" name="label" value="${h(n.label)}" maxlength="120" required></div><div class="field"><label for="node-category">分類</label><select id="node-category" name="category">${CATEGORIES.map(c=>`<option value="${c}" ${c===n.category?'selected':''}>${h(CATEGORY_LABELS[c])}</option>`).join('')}</select></div>${n.kind==='resource'?`<div class="field"><label for="node-initial">独立した初期条件の状態</label><select id="node-initial" name="initial">${Object.entries(INITIAL_LABELS).map(([s,l])=>`<option value="${s}" ${s===n.initial?'selected':''}>${h(l)}</option>`).join('')}</select></div>`:'<div class="field"><span class="field-label">種類</span><span class="help-text">経路が未定義なら情報不足。<br>成立する経路が1つでもあれば実行可能。</span></div>'}<div class="field"><label for="node-owner">担当（部署・役割）</label><input id="node-owner" name="owner" value="${h(n.owner)}" maxlength="160"></div><div class="field"><label for="node-system">SYSID / 管理番号</label><input id="node-system" name="systemId" value="${h(n.systemId)}" maxlength="120"></div><div class="field span-2"><label for="node-notes">確認上の補足（秘密値は入力しない）</label><textarea id="node-notes" name="notes" maxlength="2000">${h(n.notes)}</textarea></div></div>${n.kind!=='resource'?`<div class="section-line"><h3>復旧経路（経路間はOR）</h3>${button('add-route','経路を追加','plus','small')}</div><p class="help-text">チェックした条件はすべて必要（AND）。別の方法がある場合は新しい経路に分けてください。切り替え操作自体に必要な条件も含めます。</p>${n.routes.length?n.routes.map((r,index)=>{const refs=flatRefs(r.requires);return `<fieldset class="route-editor"><legend>経路 ${index+1}</legend><div class="route-editor-header"><input name="route-label-${index}" aria-label="経路${index+1}の名前" value="${h(r.label)}" maxlength="160">${button('remove-route','経路を削除','trash','small ghost',`data-index="${index}"`)}</div>${refs!==null?`<div class="check-grid">${uiState.model.nodes.map(candidate=>`<label class="check-label"><input type="checkbox" name="route-ref-${index}" value="${candidate.id}" ${refs.includes(candidate.id)?'checked':''}>${h(candidate.label)}${candidate.id===n.id?'（自分自身）':''}</label>`).join('')}</div>`:`<p class="help-text">入れ子の条件式です。式を保持してJSONで編集します。</p><textarea class="json-editor" name="route-expr-${index}" aria-label="経路${index+1}の条件式">${h(JSON.stringify(r.requires,null,2))}</textarea>`}</fieldset>`;}).join(''):'<div class="empty-note">まだ経路がありません。保存した場合は情報不足として判定します。</div>'}`:''}<div class="section-line"><h3>訓練・確認の記録（構成判定とは別）</h3></div><p class="help-text">成功記録には日付・確認者・証跡参照・シナリオIDが必要です。機器への接続や証跡の検証はしません。</p><div class="form-grid"><div class="field"><label for="evidence-status">結果</label><select id="evidence-status" name="ev-status">${[['not-tested','未訓練'],['passed','指定範囲の確認に成功'],['failed','失敗']].map(([v,l])=>`<option value="${v}" ${e.status===v?'selected':''}>${l}</option>`).join('')}</select></div><div class="field"><label for="evidence-date">確認日</label><input id="evidence-date" type="date" name="ev-date" value="${h(e.checkedAt||'')}"></div><div class="field"><label for="evidence-reviewer">確認者</label><input id="evidence-reviewer" name="ev-reviewer" value="${h(e.reviewer||'')}" maxlength="160"></div><div class="field"><label for="evidence-ref">証跡の参照番号・所在</label><input id="evidence-ref" name="ev-reference" value="${h(e.reference||'')}" maxlength="500"></div><div class="field"><label for="evidence-scope">検証したシナリオID</label><input id="evidence-scope" name="ev-scope" value="${h(e.scope||uiState.scenarioId)}" maxlength="160"></div><div class="field"><label for="evidence-age">再確認までの日数</label><input id="evidence-age" type="number" min="1" max="3650" name="ev-age" value="${e.maxAgeDays??90}"></div><div class="field span-2"><label class="check-label"><input type="checkbox" name="ev-bind" id="evidence-bind">今回の構成・指定シナリオで確認した記録として紐付ける</label><span class="help-text">実際に確認済みの場合のみ選択。構成・障害条件が変わると再確認が必要になります。これは証跡の真正性を保証する署名ではありません。</span></div><div class="field span-2"><label for="evidence-notes">検証範囲・結果の補足</label><textarea id="evidence-notes" name="ev-notes" maxlength="1000">${h(e.notes||'')}</textarea></div></div></div><footer class="dialog-footer"><span class="help-text">秘密情報は入力しないでください。</span><div class="group">${button('close-dialog','キャンセル','','','data-dialog="node-dialog"')}<button type="submit" class="button primary">変更を適用</button></div></footer></form>`;
}
function captureNode(){
  const f=new FormData($('#node-form')),n=structuredClone(editingNode.draft);
  for(const k of ['id','label','category','owner','systemId','notes'])n[k]=String(f.get(k)??'');
  if(n.kind==='resource')n.initial=String(f.get('initial'));
  else n.routes=n.routes.map((route,i)=>{
    const json=f.get(`route-expr-${i}`);let expr;
    if(json!==null){try{expr=JSON.parse(String(json));}catch{throw new Error(`経路${i+1}の条件式が正しいJSONではありません。`);}}
    else {
      const selected=f.getAll(`route-ref-${i}`).map(String),original=new Set(flatRefs(route.requires));
      // Checkbox order follows the node list, not the stored expression. Keep
      // unchanged conditions byte-for-byte so metadata edits do not rebind evidence.
      expr=selected.length===original.size&&selected.every(id=>original.has(id))?route.requires:{all:selected.map(ref=>({ref}))};
    }
    return {...route,label:String(f.get(`route-label-${i}`)??''),requires:expr};
  });
  n.evidence={status:String(f.get('ev-status')),scope:String(f.get('ev-scope')??''),reviewer:String(f.get('ev-reviewer')??''),reference:String(f.get('ev-reference')??''),maxAgeDays:Number(f.get('ev-age')),notes:String(f.get('ev-notes')??'')};
  if(editingNode.draft.evidence?.conditionHash)n.evidence.conditionHash=editingNode.draft.evidence.conditionHash;
  if(f.get('ev-date'))n.evidence.checkedAt=String(f.get('ev-date'));
  return n;
}
function saveNode(){
  const nextNode=captureNode(),m=structuredClone(uiState.model);
  if(editingNode.originalId)m.nodes[m.nodes.findIndex(n=>n.id===editingNode.originalId)]=nextNode;else m.nodes.push(nextNode);
  if($('#evidence-bind').checked&&nextNode.evidence.status!=='not-tested'){
    const scenario=m.scenarios.find(s=>s.id===nextNode.evidence.scope);
    if(!scenario)throw new Error('紐付けるシナリオIDが存在しません。既存シナリオのIDを指定してください。');
    nextNode.evidence.conditionHash=conditionFingerprint(validateModel(m),scenario);
  }
  const validated=validateModel(m);
  uiState.selected=nextNode.id;commitModel(validated);$('#node-dialog').close();toast('条件と記録を更新しました。構成上の判定と訓練記録は別に扱います。');
}
function openScenario(isNew=false){
  const original=isNew?null:uiState.model.scenarios.find(s=>s.id===uiState.scenarioId);
  editingScenario={originalId:original?.id??null};
  const s=original??{id:`scenario-${Date.now().toString(36)}`,name:'新しい障害シナリオ',description:'',unavailable:[],unknown:[]};
  $('#scenario-dialog').innerHTML=`<form id="scenario-form"><header class="dialog-header"><div><p class="eyebrow">OUTAGE CONDITIONS</p><h2 id="scenario-dialog-title">障害条件を編集</h2></div>${button('close-dialog','閉じる','close','ghost','data-dialog="scenario-dialog"')}</header><div class="dialog-body"><div class="form-grid"><div class="field"><label for="scenario-id">シナリオID</label><input id="scenario-id" name="id" value="${h(s.id)}" ${original?'readonly':''} required maxlength="64"></div><div class="field"><label for="scenario-name">表示名</label><input id="scenario-name" name="name" value="${h(s.name)}" required maxlength="160"></div><div class="field span-2"><label for="scenario-description">想定する障害・範囲</label><textarea id="scenario-description" name="description" maxlength="2000">${h(s.description)}</textarea></div></div><div class="wide-note">強制停止はシナリオ全体で優先されます。停止中の要素を復旧する場合、復旧操作と復旧後の能力を別ノードで表現してください。</div>${uiState.model.nodes.map(n=>`<div class="scenario-row"><label for="override-${n.id}">${h(n.label)}<small>${h(n.id)} / ${h(KIND_LABELS[n.kind])}</small></label><select id="override-${n.id}" name="override-${n.id}"><option value="unchanged" ${!s.unavailable.includes(n.id)&&!s.unknown.includes(n.id)?'selected':''}>元の条件を使用</option><option value="unavailable" ${s.unavailable.includes(n.id)?'selected':''}>強制停止</option><option value="unknown" ${s.unknown.includes(n.id)?'selected':''}>状態不明</option></select></div>`).join('')}</div><footer class="dialog-footer"><span class="help-text">実際のシステムは操作しません。</span><div class="group">${original?button('delete-scenario','シナリオ削除','trash','danger small'):''}<button type="submit" class="button primary">シナリオを適用</button></div></footer></form>`;
  $('#scenario-dialog').showModal();
}
function saveScenario(){
  const f=new FormData($('#scenario-form')),s={id:String(f.get('id')),name:String(f.get('name')),description:String(f.get('description')),unavailable:[],unknown:[]};
  for(const n of uiState.model.nodes){const override=f.get(`override-${n.id}`);if(override==='unavailable'||override==='unknown')s[override].push(n.id);}
  const m=structuredClone(uiState.model);if(editingScenario.originalId)m.scenarios[m.scenarios.findIndex(x=>x.id===editingScenario.originalId)]=s;else m.scenarios.push(s);
  validateModel(m);uiState.scenarioId=s.id;commitModel(m);$('#scenario-dialog').close();toast('障害条件を更新し、再評価しました。');
}
function openJson(){
  $('#json-dialog').innerHTML=`<header class="dialog-header"><div><p class="eyebrow">VERSIONED MODEL / JSON</p><h2 id="json-dialog-title">モデルJSON</h2></div>${button('close-dialog','閉じる','close','ghost','data-dialog="json-dialog"')}</header><div class="dialog-body"><p class="help-text">入れ子のAND/ORやモデル名を編集できます。不正な入力は適用せず、元のモデルを保持します。</p><textarea id="json-text" class="json-editor" aria-label="モデルJSONの内容" spellcheck="false">${h(JSON.stringify(uiState.model,null,2))}</textarea></div><footer class="dialog-footer"><span class="help-text">上限1 MiB / 250要素 / 資格情報は入力しない</span>${button('apply-json','JSONを適用','check','primary')}</footer>`;
  $('#json-dialog').showModal();
}
function exportFile(name,text,type){
  const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
function confirmReplace(){return !uiState.dirty||confirm('メモリ上のモデルを置き換えます。必要な変更は先にJSON保存してください。続けますか？');}
function handleAction(action,el){
  if(action==='tab'){uiState.tab=el.dataset.tab;render();return;}
  if(action==='select-node'){uiState.selected=el.dataset.id;render();return;}
  if(action==='import'){$('#import-file').click();return;}
  if(action==='export-model'){exportFile('breakglassmap-model.json',JSON.stringify(uiState.model,null,2),'application/json');toast('モデルJSONを書き出しました。構成情報を含むため、保管先に注意してください。');return;}
  if(action==='export-result'){exportFile('breakglassmap-analysis.json',JSON.stringify(analysis,null,2),'application/json');return;}
  if(action==='export-csv'){exportFile('breakglassmap-checklist.csv',toCsv(uiState.model,analysis),'text/csv;charset=utf-8');return;}
  if(action==='export-html'){exportFile('breakglassmap-report.html',toHtml(uiState.model,analysis),'text/html;charset=utf-8');return;}
  if(action==='whatif'){
    const m=structuredClone(uiState.model);uiState.comparison={model:structuredClone(m),scenarioId:uiState.scenarioId,before:structuredClone(analysis)};
    for(const id of ['offline-kit','offline-runbook'])m.nodes.find(n=>n.id===id).initial='available';
    commitModel(m,{keepComparison:true});toast('独立した手段を「利用可能」と仮定しました。実機確認や訓練記録は変更していません。');return;
  }
  if(action==='undo-whatif'){const previous=uiState.comparison;uiState.scenarioId=previous.scenarioId;commitModel(previous.model);toast('変更前のモデルに戻しました。');return;}
  if(action==='load-demo'||action==='new-model'){
    if(!confirmReplace())return;
    uiState.tab=action==='load-demo'?'overview':'model';uiState.selected=action==='load-demo'?'goal-identity':'goal-1';commitModel(action==='load-demo'?structuredClone(DEMO):emptyModel(),{resetScenario:true});return;
  }
  if(action==='edit-node'){openNode(el.dataset.id);return;}
  if(action==='add-node'){openNode(null,el.dataset.kind);return;}
  if(action==='delete-node'){
    const id=el.dataset.id,refs=uiState.model.nodes.filter(n=>(n.routes??[]).some(r=>listRefs(r.requires).includes(id)));
    if(refs.length)throw new Error(`他の経路から参照されています：${refs.map(n=>n.label).join('、')}。先に参照を解除してください。`);
    if(!confirm('この要素と対応する訓練記録を削除しますか？'))return;
    const m=structuredClone(uiState.model);m.nodes=m.nodes.filter(n=>n.id!==id);for(const s of m.scenarios){s.unavailable=s.unavailable.filter(x=>x!==id);s.unknown=s.unknown.filter(x=>x!==id);}commitModel(m);return;
  }
  if(action==='close-dialog'){$(`#${el.dataset.dialog}`).close();return;}
  if(action==='add-route'){editingNode.draft=captureNode();if(editingNode.draft.routes.length>=LIMITS.routes)throw new Error('経路は16件までです。');editingNode.draft.routes.push({id:`route-${Date.now().toString(36)}`,label:`代替経路 ${editingNode.draft.routes.length+1}`,requires:{all:[]}});renderNodeDialog();return;}
  if(action==='remove-route'){editingNode.draft=captureNode();editingNode.draft.routes.splice(Number(el.dataset.index),1);renderNodeDialog();return;}
  if(action==='edit-scenario'||action==='new-scenario'){openScenario(action==='new-scenario');return;}
  if(action==='delete-scenario'){
    if(uiState.model.scenarios.length===1)throw new Error('少なくとも1つのシナリオを残してください。');
    if(!confirm('このシナリオを削除しますか？対応する訓練記録の範囲は自動変更しません。'))return;
    const m=structuredClone(uiState.model);m.scenarios=m.scenarios.filter(s=>s.id!==editingScenario.originalId);commitModel(m,{resetScenario:true});$('#scenario-dialog').close();return;
  }
  if(action==='edit-json'){openJson();return;}
  if(action==='apply-json'){const m=parseModel($('#json-text').value);commitModel(m);$('#json-dialog').close();toast('モデルJSONを適用しました。');return;}
  if(action==='filter'){uiState.filter=el.dataset.filter;render();return;}
}
// Event delegation keeps rendering deterministic. No user text is executable markup.
document.addEventListener('click',event=>{
  const el=event.target.closest('[data-action]');if(!el)return;
  try{handleAction(el.dataset.action,el);}catch(error){toast(error.message,true);}
});
document.addEventListener('keydown',event=>{
  if((event.key==='Enter'||event.key===' ')&&event.target.matches('g[role="button"]')){event.preventDefault();event.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}
});
document.addEventListener('submit',event=>{
  // Form controls named `id` shadow HTMLFormElement.id; read the attribute.
  const formId=event.target.getAttribute('id');
  if(!['node-form','scenario-form'].includes(formId))return;event.preventDefault();
  try{if(formId==='node-form')saveNode();else saveScenario();}catch(error){toast(error.message,true);}
});
document.addEventListener('change',event=>{
  try{
    if(event.target.id==='scenario-select'){uiState.scenarioId=event.target.value;uiState.custom=null;uiState.comparison=null;persist();render();}
    if(event.target.id==='as-of'){if(!validDate(event.target.value))throw new Error('評価基準日を入力してください。');uiState.asOf=event.target.value;persist();render();}
    if(event.target.id==='persist-toggle'){
      if(event.target.checked){uiState.persist=true;persist();toast('このブラウザに構成情報を未暗号化で保存します。共有端末では利用しないでください。');}
      else{uiState.persist=false;try{localStorage.removeItem(OPTIN_KEY);localStorage.removeItem(STORAGE_KEY);}catch{}toast('このアプリのブラウザ保存データを削除しました。メモリ上のモデルは残ります。');}render();
    }
  }catch(error){toast(error.message,true);render();}
});
document.addEventListener('input',event=>{
  if(event.target.id==='check-search'){const position=event.target.selectionStart;uiState.search=event.target.value;render();const input=$('#check-search');input.focus();if(position!==null)input.setSelectionRange(position,position);}
});
$('#import-file').addEventListener('change',async event=>{
  const file=event.target.files?.[0];if(!file)return;
  try{if(file.size>LIMITS.bytes)throw new Error('入力ファイルは1 MiB以下にしてください。');const candidate=parseModel(await file.text());if(!confirmReplace())return;commitModel(candidate,{resetScenario:true});toast('JSONモデルを読み込みました。内容は外部送信していません。');}
  catch(error){toast(`読み込みを中止しました：${error.message}`,true);}finally{event.target.value='';}
});
restoreStored();
render();
