"""Self-contained, escaped HTML and spreadsheet-safe CSV exports."""
from __future__ import annotations
import base64
import csv
import hashlib
import io
from html import escape
from importlib.resources import files
from urllib.parse import urlsplit

STATUS_JA={'PASSED':'成立（モデル上）','FAILED':'不成立','UNKNOWN':'情報不足','NOT_APPLICABLE':'対象外'}
ASSURANCE_JA={'none':'根拠不足','self_reported':'自己申告','configuration':'設定証跡の申告','tested':'試験証跡の申告'}
OVERALL_JA={'NEEDS_REMEDIATION':'設計上の要確認事項があります','INSUFFICIENT_EVIDENCE':'成立判断に必要な証跡が不足しています','MODEL_CHECKS_SATISFIED':'登録モデル上の点検条件を満たしています'}
REPORT_JS="""document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.finding').forEach(x=>x.hidden=b.dataset.filter!=='all'&&x.dataset.status!==b.dataset.filter)}));document.getElementById('expand')?.addEventListener('click',()=>document.querySelectorAll('.finding').forEach(x=>x.open=true));document.getElementById('print')?.addEventListener('click',()=>{document.querySelectorAll('.finding').forEach(x=>{x.hidden=false;x.open=true});window.print()});"""


def e(value): return escape(str(value),quote=True)


def safe_href(url):
    try:
        parts=urlsplit(url)
        return url if parts.scheme=='https' and parts.netloc and not parts.username else '#'
    except (TypeError,ValueError): return '#'


def badge(status): return f'<span class="pill {e(status)}">{e(STATUS_JA.get(status,status))}</span>'


def page(title,body,script=REPORT_JS):
    css=files('cleanroomcheck').joinpath('web','common.css').read_text(encoding='utf-8')
    digest=base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp=f"default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'; object-src 'none'"
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{e(csp)}"><title>{e(title)}</title><style>{css}</style></head><body>{body}<script>{script}</script></body></html>'


def metrics(summary):
    cls={'FAILED':'failed','UNKNOWN':'unknown','PASSED':'passed','NOT_APPLICABLE':'na'}
    return '<div class="metrics">'+''.join(f'<div class="metric {cls[s]}"><div class="label">{e(STATUS_JA[s])}</div><div class="number">{summary[s]}</div><div class="section-note">点検結果数</div></div>' for s in cls)+'</div>'


def masthead(project,subheading,meta):
    return f'<header class="masthead"><div class="wrap"><div class="brand"><span class="mark">C/R</span>CleanRoomCheck <span class="eyebrow">ALPHA</span></div><h1>{e(project)}</h1><p>{e(subheading)}</p><div class="meta">{meta}</div></div></header>'


def _path_text(path,nodes):
    if not path: return '対象自体がこのシナリオの侵害起点として指定されています。'
    parts=[nodes.get(path[0]['source'],path[0]['source'])]
    for edge in path:
        relation=edge['relation']+(' / Azure GA推論' if edge.get('inferred') else '')
        parts.append(f' —[{relation}]→ '+nodes.get(edge['target'],edge['target']))
    return ''.join(parts)


def _finding(f,nodes,sources):
    rows=[]
    for p in f['facts']:
        value='未確認' if p['value'] is None else str(p['value']).lower() if type(p['value']) is bool else str(p['value'])
        notes=' / '.join(p['notes'])
        rows.append(f'<tr><td>{e(p["label"])}<br><code>{e(p["field"])}</code></td><td>{e(value)}</td><td>{e(ASSURANCE_JA[p["level"]])}<br>{e(", ".join(p["evidence_ids"]) or "—")}</td><td>{e(notes or "分類・鮮度条件内（内容未検証）")}</td></tr>')
    table='<div class="scroll"><table><thead><tr><th>確認項目</th><th>入力値</th><th>証跡</th><th>照合結果</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>' if rows else ''
    paths=''.join(f'<div class="path">{e(_path_text(path,nodes))}</div>' for path in f['paths'])
    path_notes='; '.join(note for p in f.get('path_evidence',[]) for note in p['notes'])
    links=' / '.join(f'<a href="{e(safe_href(sources[sid]["url"]))}" target="_blank" rel="noopener noreferrer">{e(sid)}</a>' for sid in f['source_ids'] if sid in sources)
    return f'''<details class="finding" data-status="{e(f['status'])}"><summary>{badge(f['status'])}<div><div class="title">{e(f['title'])}</div><div class="sub">{e(f['rule_id'])} · {e(f['assessment_name'])} / {e(f['scenario_name'])}</div></div><span class="spacer"></span><small>{e(ASSURANCE_JA[f['assurance']])}</small></summary><div class="body"><p class="message">{e(f['message'])}</p>{paths}<small>{e(path_notes)}</small>{table}<div class="action"><strong>設計・確認アクション</strong><br>{e(f['remediation'])}<br><strong>確認質問</strong><br>{e(f['question'])}</div><div class="source-line">根拠: {links}<br>{e(f['evidence_note'])}</div></div></details>'''


def render_html(result: dict) -> str:
    nodes={n['id']:n['label'] for n in result['nodes']}; sources={s['id']:s for s in result['sources']}
    meta=f'<span>評価基準日 {e(result["as_of"])}</span><span>Ruleset {e(result["ruleset_version"])}</span><span>証跡許容期間 {result["max_evidence_age_days"]}日</span><span>{len(result["scenarios"])}シナリオ</span>'
    head=masthead(result['project']['name'],'クラウドテナント侵害を想定した、分離境界・保管・復旧経路の設計点検',meta)
    demo='<div class="notice demo"><strong>架空環境デモ</strong> — 構成値・証跡・試験記録はすべて説明用の仮定です。実顧客の環境・導入事例・実機試験結果ではありません。</div>' if result['project']['demo'] else ''
    zones=[]
    for plane,label in [('production','本番 / Production'),('backup','保管 / Backup'),('recovery','復旧 / Recovery'),('shared','共有 / Shared')]:
        entries=[n for n in result['nodes'] if n['plane']==plane]
        cards=''.join(f'<div class="node">{e(n["label"])}<span>{e(n["id"])} · {e(n["kind"])}{(" · tenant="+e(n["tenant"])) if n.get("tenant") else ""}</span></div>' for n in entries[:12])
        if len(entries)>12: cards+=f'<p class="section-note">ほか{len(entries)-12}件（全件はJSONを参照）</p>'
        zones.append(f'<div class="zone"><h3>{e(label)}</h3>{cards or "<small>登録なし</small>"}</div>')
    scenarios=''.join(f'<tr><td>{e(s["name"])}</td><td>{e(", ".join(s["compromised"]))}</td><td>{e(", ".join(s.get("azure_global_admin_tenants",[])) or "推論なし")}</td></tr>' for s in result['scenarios'])
    source_list=''.join(f'<li><a href="{e(safe_href(s["url"]))}" target="_blank" rel="noopener noreferrer">{e(s["id"])} — {e(s["title"])}</a><div class="source-note">{e(s["publisher"])} / 確認 {e(s["verified_on"])} · {e(s["scope_note"])}</div></li>' for s in result['sources'])
    evidence_rows=''.join(f'<tr><td>{e(ev["id"])}</td><td>{e(ASSURANCE_JA[ev["type"]])}</td><td>{e(ev["collected_at"])}</td><td>{e(ev["reference"])}</td></tr>' for ev in result['evidence'])
    controls='<div class="toolbar no-print"><button class="active" data-filter="all">すべて</button>'+''.join(f'<button data-filter="{s}">{e(STATUS_JA[s])}</button>' for s in ['FAILED','UNKNOWN','PASSED'])+'<span class="spacer"></span><button id="expand">詳細を開く</button><button id="print">印刷</button></div>'
    finding_html=''.join(_finding(f,nodes,sources) for f in sorted(result['findings'],key=lambda f:({'FAILED':0,'UNKNOWN':1,'PASSED':2,'NOT_APPLICABLE':3}[f['status']],f['scenario_id'],f['assessment_id'],f['rule_id'])))
    body=f'''{head}<main class="wrap">{demo}<div class="notice"><strong>{e(OVERALL_JA[result['overall']])}</strong><br>{e(result['disclaimer'])}</div>{metrics(result['summary'])}<p class="section-note">件数は業務×シナリオ×ルール単位です。合算した安全スコアではありません。「成立」は証跡メタデータと入力値の条件を満たす意味です。</p><h2>01 / 評価した境界と侵害条件</h2><div class="panel"><p class="section-note">以下は登録資産の論理的な配置です。区画名そのものは、分離を保証しません。</p><div class="zones">{''.join(zones)}</div><div class="scroll"><table><thead><tr><th>シナリオ</th><th>侵害起点</th><th>全体管理者を仮定するAzure tenant</th></tr></thead><tbody>{scenarios}</tbody></table></div></div><h2>02 / 点検結果と設計アクション</h2>{controls}{finding_html}<h2>03 / 登録された証跡メタデータ</h2><div class="panel"><p class="section-note">本ツールは参照先ファイルを開かず、入力された種別と日付を照合します。実体のレビュー、対象範囲との一致、署名・真正性は人が確認してください。</p><div class="scroll"><table><thead><tr><th>ID</th><th>申告された種別</th><th>取得/試験日</th><th>参照先（自動取得なし）</th></tr></thead><tbody>{evidence_rows}</tbody></table></div></div><h2>04 / 一次資料と適用範囲</h2><div class="panel"><p>点検項目は本OSSの設計レビュー方針です。公式資料は技術的な前提の参照先であり、本OSSの判定や個別構成を認定するものではありません。</p><ol class="sources">{source_list}</ol></div><footer>CleanRoomCheck {e(result['tool_version'])} / Ruleset {e(result['ruleset_version'])}<br>正規化入力 SHA-256: <code>{e(result['input_sha256'])}</code><br>データ不変性・管理面の分離・復元可否・クリーン性は別々の条件です。実環境への適用前に専門家レビューと隔離環境での実証を実施してください。</footer></main>'''
    return page('CleanRoomCheck — '+result['project']['name'],body)


def safe_csv_cell(value):
    value=str(value)
    if value.lstrip(' \t\r\n').startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n')):
        return "'"+value
    return value


def csv_text(headers,rows):
    stream=io.StringIO(newline=''); writer=csv.writer(stream)
    writer.writerow(headers)
    for row in rows: writer.writerow([safe_csv_cell(cell) for cell in row])
    return stream.getvalue()


def questions_csv(result):
    rows=[]
    for f in result['findings']:
        if f['status'] not in {'FAILED','UNKNOWN'}: continue
        rows.append([f['assessment_name'],f['scenario_name'],f['rule_id'],STATUS_JA[f['status']],f['severity'],f['question'],f['remediation'],'','',''])
    return csv_text(['業務','侵害シナリオ','ルールID','判定','優先度','ベンダー/担当者への質問','確認・改善案','回答','根拠資料','担当者'],rows)


def verification_csv(result):
    rows=[]
    for f in result['findings']:
        if f['phase']!='validation' or f['status']=='NOT_APPLICABLE': continue
        rows.append([f['assessment_name'],f['scenario_name'],f['rule_id'],f['title'],STATUS_JA[f['status']],f['question'],'','','',''])
    return csv_text(['業務','侵害シナリオ','ルールID','検証項目','現在判定','検証で確認すること','担当者','実施日','結果','証跡参照'],rows)
