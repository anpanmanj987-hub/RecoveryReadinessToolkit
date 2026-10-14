import {STATUS_LABELS,EVIDENCE_LABELS} from './engine.mjs';
export function escapeHtml(value) {return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function reportCell(value) {
  let s=String(value??'');
  if(/^[\s\uFEFF]*[=+\-@]|^[\t\r\n]/.test(s))s="'"+s;
  return '"'+s.replace(/"/g,'""')+'"';
}
export function toCsv(model,analysis) {
  const headers=['priority','item_id','node_id','label','owner','system_id','code','status','affected_goals','question','evidence_date','evidence_reviewer','evidence_reference','evidence_scope','scenario_id','as_of'];
  const rows=analysis.checklist.map(i=>[i.priority,i.id,i.nodeId,i.label,i.owner,i.systemId,i.code,i.status,i.affectedGoals.join(' | '),i.question,i.evidence.checkedAt,i.evidence.reviewer,i.evidence.reference,i.evidence.scope,analysis.scenario.id,analysis.asOf]);
  return '\uFEFF'+[headers,...rows].map(row=>row.map(reportCell).join(',')).join('\r\n')+'\r\n';
}
export function toText(model,analysis) {
  const names=new Map(model.nodes.map(n=>[n.id,n.label]));
  const lines=[`BreakGlassMap ${analysis.toolVersion}`,`${model.name}`,`Scenario: ${analysis.scenario.name} [${analysis.scenario.id}] | As of: ${analysis.asOf}`,'',`GOALS: ready=${analysis.summary.ready} blocked=${analysis.summary.blocked} unknown=${analysis.summary.unknown}`];
  for(const g of analysis.goals) {
    lines.push(`- [${g.status} / ${STATUS_LABELS[g.status]}] ${g.label} (${g.id})`);
    for(const id of g.blockers??[])lines.push(`    unmet: ${names.get(id)} (${id})`);
  }
  for(const c of analysis.cycles.filter(x=>x.affectedGoals.length))lines.push(`- Circular conditions: ${c.nodes.join(' <-> ')}; unresolved goals: ${c.affectedGoals.join(', ')}`);
  lines.push('','CHECKLIST');
  for(const i of analysis.checklist)lines.push(`[${i.priority}] ${i.label} — ${i.question} | owner: ${i.owner||'unassigned'}`);
  lines.push('','LIMITATIONS',...analysis.limitations.map(x=>`- ${x}`));
  return lines.join('\n')+'\n';
}
export function toHtml(model,analysis) {
  const h=escapeHtml;
  const goalRows=analysis.goals.map(g=>`<tr><td>${h(g.label)}<small>${h(g.id)}</small></td><td class="${g.status}">${h(STATUS_LABELS[g.status])}</td><td>${h(g.owner||'未設定')}</td><td>${h(EVIDENCE_LABELS[g.evidenceStatus])}</td></tr>`).join('');
  const checkRows=analysis.checklist.map(i=>`<tr><td>${h(i.priority)}</td><td>${h(i.label)}<small>${h(i.nodeId)}</small></td><td>${h(i.question)}</td><td>${h(i.owner||'未設定')}</td><td>${h(i.evidence.checkedAt||'—')}<small>${h(i.evidence.reference||'')}</small></td></tr>`).join('');
  const routeRows=analysis.nodes.map(n=>`<h3>${h(n.label)} <span class="${n.status}">${h(STATUS_LABELS[n.status])}</span></h3><p>担当: ${h(n.owner||'未設定')} / ${h(n.systemId||'SYSID未設定')} / 訓練記録: ${h(EVIDENCE_LABELS[n.evidenceStatus])}</p>${n.routes.length?'<ul>'+n.routes.map(r=>`<li>${h(r.label)}: ${h(STATUS_LABELS[r.status])} — ${r.dependencies.map(d=>`${h(d.id)} (${h(STATUS_LABELS[d.status])})`).join(', ')}</li>`).join('')+'</ul>':'<p>独立した初期条件、または未定義の経路。詳細は入力モデルを参照。</p>'}`).join('');
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>BreakGlassMap — ${h(model.name)}</title><style>body{font:15px/1.7 system-ui,sans-serif;color:#1d2935;max-width:1120px;margin:40px auto;padding:0 28px}h1{font-size:36px;letter-spacing:-1px}h2{margin-top:36px}h3{font-size:16px}small{display:block;color:#667580}table{border-collapse:collapse;width:100%;margin:20px 0}th,td{padding:12px;text-align:left;border-bottom:1px solid #dde4e7;vertical-align:top}th{background:#edf2f1}.ready{color:#11735d}.blocked{color:#b64235}.unknown{color:#95600d}.note{padding:16px;background:#f5f4ec;border-left:4px solid #a68b38}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f5;padding:16px}p{overflow-wrap:anywhere}@media print{body{margin:0;font-size:10pt}tr{break-inside:avoid}details{display:none}}</style></head><body><small>BREAKGLASSMAP / RECOVERY READINESS · ${h(analysis.toolVersion)}</small><h1>${h(model.name)}</h1><p>${h(analysis.scenario.name)} [${h(analysis.scenario.id)}] · 評価基準日 ${h(analysis.asOf)}</p><div class="note">${analysis.limitations.map(x=>h(x)).join('<br>')}<br>このレポートは構成情報を含みます。承認された場所に保管してください。</div><h2>復旧目標</h2><table><thead><tr><th>目標</th><th>構成上の判定</th><th>担当</th><th>訓練記録（別軸）</th></tr></thead><tbody>${goalRows}</tbody></table><h2>選択した障害条件</h2><p>強制停止: ${h(analysis.scenario.unavailable.join(', ')||'なし')}<br>状態不明: ${h(analysis.scenario.unknown.join(', ')||'なし')}</p><h2>確認・訓練チェックリスト</h2><table><thead><tr><th>優先度</th><th>対象</th><th>確認事項</th><th>担当</th><th>日付・証跡</th></tr></thead><tbody>${checkRows}</tbody></table><h2>経路と判定根拠</h2>${routeRows}<h2>構造上の循環</h2>${analysis.cycles.length?analysis.cycles.map(c=>`<p>${h(c.nodes.join(' ↔ '))}<br>未解決目標への関連: ${h(c.affectedGoals.join(', ')||'なし（代替経路等で成立）')}</p>`).join(''):'<p>入力モデルでは検出なし。</p>'}<details><summary>入力モデル（再現用。内容は未暗号化）</summary><pre>${h(JSON.stringify(model,null,2))}</pre></details><footer><hr><small>Generated locally by BreakGlassMap. No environment access, recovery execution, or independent evidence validation.</small></footer></body></html>`;
}
