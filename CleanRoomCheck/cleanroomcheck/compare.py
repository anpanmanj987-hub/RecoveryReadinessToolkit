"""Scope-aware comparison: deleting a check or weakening a threat is not a fix."""
from __future__ import annotations
from .model import ModelError
from .report import e, badge, page, masthead, metrics

CHANGE_JA={'resolved_in_model':'入力モデル上の解消','regressed':'判定の悪化','evidence_completed':'証跡の充足','evidence_regressed':'証跡の不足化','unverified_change':'未検証の変更','scope_changed':'評価範囲の変更','added':'点検対象の追加','removed':'点検対象の削除','unchanged':'変更なし'}


def _scenario_signature(s):
    return (tuple(sorted(s['compromised'])),tuple(sorted(s.get('azure_global_admin_tenants',[]))))


def compare_results(before: dict, after: dict) -> dict:
    for field in ('report_version','tool_version','ruleset_version','as_of','max_evidence_age_days'):
        if before.get(field)!=after.get(field): raise ModelError(f'比較条件が異なります: {field}')
    if before['project']['id']!=after['project']['id']: raise ModelError('異なるproject.idは比較できません')
    old={f['id']:f for f in before['findings']}; new={f['id']:f for f in after['findings']}
    bs={s['id']:_scenario_signature(s) for s in before['scenarios']}; ns={s['id']:_scenario_signature(s) for s in after['scenarios']}
    scope_changed={sid for sid in set(bs)|set(ns) if bs.get(sid)!=ns.get(sid)}
    scope_before={a['id']:(a['provider'],a['workload']) for a in before.get('assessment_scopes',[])}
    scope_after={a['id']:(a['provider'],a['workload']) for a in after.get('assessment_scopes',[])}
    changed_assessments={aid for aid in set(scope_before)|set(scope_after) if scope_before.get(aid)!=scope_after.get(aid)}
    changes=[]
    for fid in sorted(set(old)|set(new)):
        a,b=old.get(fid),new.get(fid); item=b or a
        x=a['status'] if a else None; y=b['status'] if b else None
        if a is None: category='added'
        elif b is None: category='removed'
        elif item['scenario_id'] in scope_changed or item['assessment_id'] in changed_assessments: category='scope_changed'
        elif x==y: category='unchanged'
        elif 'NOT_APPLICABLE' in (x,y): category='scope_changed'
        elif x=='FAILED' and y=='PASSED': category='resolved_in_model'
        elif x=='FAILED' and y=='UNKNOWN': category='unverified_change'
        elif y=='FAILED': category='regressed'
        elif x=='UNKNOWN' and y=='PASSED': category='evidence_completed'
        elif x=='PASSED' and y=='UNKNOWN': category='evidence_regressed'
        else: category='unverified_change'
        changes.append({'id':fid,'rule_id':item['rule_id'],'title':item['title'],'assessment_name':item['assessment_name'],'scenario_name':item['scenario_name'],
                        'before':x,'after':y,'change':category,'before_message':a['message'] if a else '', 'after_message':b['message'] if b else ''})
    return {'comparison_version':'1.0','project':after['project'],'as_of':after['as_of'],
            'ruleset_version':after['ruleset_version'],'summary':{k:sum(x['change']==k for x in changes) for k in CHANGE_JA},
            'before_summary':before['summary'],'after_summary':after['summary'],
            'before_sha256':before['input_sha256'],'after_sha256':after['input_sha256'],
            'changes':changes,'disclaimer':'入力・証跡の変更によるモデル上の比較です。実環境の改善効果や安全性の実証ではありません。'}


def render_comparison(data):
    head=masthead(data['project']['name']+' / 構成比較','変更前と変更後を同一基準日・同一ルールで比較',f'<span>評価基準日 {e(data["as_of"])}</span><span>Ruleset {e(data["ruleset_version"])}</span>')
    changes=[]
    for c in data['changes']:
        if c['change']=='unchanged': continue
        changes.append(f'<div class="comparison-change"><div class="delta">{e(CHANGE_JA[c["change"]])} · {e(c["title"])}</div><small>{e(c["rule_id"])} · {e(c["assessment_name"])} / {e(c["scenario_name"])}</small><p>{badge(c["before"]) if c["before"] else "未存在"} → {badge(c["after"]) if c["after"] else "削除"}</p><p class="section-note">変更後: {e(c["after_message"] or "点検対象が削除されています。改善とは扱いません。")}</p></div>')
    summary=''.join(f'<tr><td>{e(label)}</td><td>{data["summary"][key]}</td></tr>' for key,label in CHANGE_JA.items())
    demo='<div class="notice demo"><strong>架空環境の比較</strong> — 実施済みの構築・試験・顧客事例ではありません。</div>' if data['project']['demo'] else ''
    body=f'''{head}<main class="wrap">{demo}<div class="notice">{e(data['disclaimer'])}<br>FAILED→UNKNOWN、点検対象の削除、侵害条件の変更は「解消」に含めません。</div><h2>変更前</h2>{metrics(data['before_summary'])}<h2>変更後</h2>{metrics(data['after_summary'])}<div class="grid-two"><div class="panel"><h3>変化の内訳</h3><table><tbody>{summary}</tbody></table></div><div class="panel"><h3>比較結果の読み方</h3><p>「入力モデル上の解消」は同じ点検で不成立から成立になったものです。入力が設計案なら、構築や試験の完了を意味しません。</p><p>不成立がなくても、情報不足が残る限り設計・検証の追加が必要です。</p><p>ここでの件数は業務×シナリオ×ルール単位です。</p></div></div><h2>変更された点検結果</h2><div class="panel">{''.join(changes) or '<p>判定の変更はありません。</p>'}</div><footer>変更前 SHA-256: <code>{e(data['before_sha256'])}</code><br>変更後 SHA-256: <code>{e(data['after_sha256'])}</code></footer></main>'''
    return page('CleanRoomCheck — 構成比較',body,script='')
