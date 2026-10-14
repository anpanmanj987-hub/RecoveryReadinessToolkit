"""Deterministic evidence-aware model review; no remote calls and no cloud writes."""
from __future__ import annotations
import hashlib
import json
from datetime import date
from copy import deepcopy
from . import __version__
from .catalog import RULES, RULESET_VERSION, LABELS, TESTED_FIELDS, load_sources
from .graph import control_paths, effect_path, network_paths
from .model import ModelError, parse_date, validate_model

STATUS=('PASSED','FAILED','UNKNOWN','NOT_APPLICABLE')
RANK={'none':0,'self_reported':1,'configuration':2,'tested':3}
DISCLAIMER='入力モデルと証跡メタデータに基づく設計点検です。実クラウド、証跡の実体・真正性、マルウェア不存在、復旧成功を保証しません。'


class Context:
    def __init__(self, model, assessment, scenario, as_of, max_age, control, network):
        self.model=model; self.a=assessment; self.scenario=scenario
        self.nodes={n['id']:n for n in model['nodes']}
        self.evidence={e['id']:e for e in model['evidence']}
        self.as_of=as_of; self.max_age=max_age; self.control=control; self.network=network

    def val(self,field): return self.a['facts'].get(field,{}).get('value')

    def proof(self,ids,required='configuration'):
        candidates=[]; notes=[]
        for eid in ids:
            e=self.evidence[eid]; age=(self.as_of-parse_date(e['collected_at'])).days
            if age<0: notes.append(f'{eid}: 評価日より未来の証跡')
            elif age>self.max_age: notes.append(f'{eid}: 証跡が古い（{age}日）')
            else: candidates.append(e['type'])
        level=max(candidates,key=lambda x:RANK[x]) if candidates else 'none'
        ok=RANK[level]>=RANK[required]
        if not ids: notes.append('証跡未登録')
        elif not ok: notes.append(f'{required}以上の有効な証跡が必要')
        return {'level':level,'adequate':ok,'required':required,'notes':notes,'evidence_ids':list(ids)}

    def field_proof(self,field):
        claim=self.a['facts'].get(field,{})
        required='tested' if field in TESTED_FIELDS else 'configuration'
        return {'field':field,'label':LABELS[field],'value':claim.get('value'),**self.proof(claim.get('evidence',[]),required)}


def decision(status,message,fields,paths=None,groups=None):
    return {'status':status,'message':message,'fields':list(fields),'paths':paths or [],'groups':groups or []}


def _booleans(c,fields):
    bad=[f for f in fields if c.val(f) is False]
    if bad: return decision('FAILED','入力上、未成立: '+'、'.join(LABELS[f] for f in bad),fields)
    missing=[f for f in fields if c.val(f) is None]
    if missing: return decision('UNKNOWN','未確認: '+'、'.join(LABELS[f] for f in missing),fields)
    return decision('PASSED','入力値では確認条件を満たします。証跡の強度・鮮度も別途照合します。',fields)


def _graph_absence(c,target,fields,relations=None,message='管理権限が復旧側に到達します。'):
    path=effect_path(c.model,c.control,target,relations or set())
    if path is not None:
        groups=[]
        for e in path: groups.extend(e.get('evidence_groups',[e.get('evidence',[])]))
        return decision('FAILED',message,[],[path],groups)
    if c.val('control_graph_complete') is not True:
        return decision('UNKNOWN','経路は未検出ですが、管理権限グラフの網羅確認がないため分離成立とは判定しません。',fields)
    return decision('PASSED','登録グラフ上、選択した侵害起点から対象へ至る管理/破壊権限経路は未検出です。',fields)


def _rule_decision(c,rule):
    fields=rule['fields']; kind=rule['kind']
    is_m365=c.a['provider']=='m365' or c.a['workload']=='m365'
    if rule['category']=='M365' and not is_m365:
        return decision('NOT_APPLICABLE','この業務はM365として登録されていません。',[])
    if kind=='all_true': return _booleans(c,fields)
    if kind=='identity':
        g=_graph_absence(c,c.a['recovery_node'],fields)
        if g['status']=='FAILED': return g
        if c.val('independent_identity') is False: return _booleans(c,['independent_identity'])
        if g['status']=='UNKNOWN': return g
        return _booleans(c,fields)
    if kind=='backup':
        return _graph_absence(c,c.a['backup_node'],fields,{'can_delete','can_disable'},'バックアップ管理面への管理/破壊権限経路があります。不変復旧点を削除できるという判定ではありません。')
    if kind=='network':
        target=c.a['recovery_node']
        if target in c.network:
            path=c.network[target]; groups=[]
            for e in path: groups.extend(e.get('evidence_groups',[e.get('evidence',[])]))
            return decision('FAILED','侵害起点またはその管理対象から、復旧側への登録済み通信経路があります。これは攻撃成功の判定ではありません。',[],[path],groups)
        if c.val('network_graph_complete') is not True:
            return decision('UNKNOWN','通信経路は未検出ですが、調査範囲の網羅確認がありません。',fields)
        return decision('PASSED','登録された通信経路では、侵害起点から復旧側に到達しません。',fields)
    if kind=='lock':
        mode=c.val('immutable_mode')
        if mode in {'none','governance','azure_unlocked'} or c.val('lock_finalized') is False:
            return decision('FAILED','不変性が未設定、解除可能、または不可逆ロックが未確定です。',fields)
        if mode is None or c.val('lock_finalized') is None:
            return decision('UNKNOWN','モードと不可逆ロックの確定状態の両方を確認してください。',fields)
        if mode=='other_locked':
            return decision('UNKNOWN','この不変方式の意味は初版ルールでは評価しません。製品仕様の個別確認が必要です。',fields)
        backup_provider=c.nodes[c.a['backup_node']]['provider']
        if (mode=='compliance' and backup_provider!='aws') or (mode=='azure_locked' and backup_provider!='azure'):
            return decision('UNKNOWN','不変モードと保管先プロバイダの対応が不明です。',fields)
        return decision('PASSED','入力上は解除不可の確定済みモードです。復旧点の保護適用・期限は別項目で確認します。',fields)
    if kind=='protection':
        value=c.val('protection_until')
        if c.val('immutable_applies_to_points') is False:
            return decision('FAILED','必要な復旧点に不変保護が適用されていません。',fields)
        if value is not None and parse_date(value)<=c.as_of:
            return decision('FAILED','不変保護の終了日が評価日以前です。当日終了も保護成立とは扱いません。',fields)
        if value is None or c.val('immutable_applies_to_points') is None:
            return decision('UNKNOWN','復旧点への適用と保護終了日がそろっていません。',fields)
        return decision('PASSED','必要な復旧点への不変保護の適用と、評価日より後の終了日が入力されています。',fields)
    if kind in {'retention','rto','rpo'}:
        pairs={'retention':('retention_days','required_retention_days'),
               'rto':('measured_rto_hours','rto_hours'), 'rpo':('measured_data_loss_hours','rpo_hours')}
        measured,objective=pairs[kind]; a,b=c.val(measured),c.val(objective)
        if a is None or b is None or (kind=='retention' and b==0):
            return decision('UNKNOWN','目標・要件と比較値を明示してください。必要保持日数0も未定義として扱います。',fields)
        ok=a>=b if kind=='retention' else a<=b
        return decision('PASSED' if ok else 'FAILED',f'{LABELS[measured]}={a} / {LABELS[objective]}={b}。'+('入力上、目標内です。' if ok else '入力上、目標を満たしません。'),fields)
    if kind=='key':
        mode=c.val('key_management')
        if mode is None: return decision('UNKNOWN','復号鍵の管理方式が不明です。',fields)
        if mode=='provider':
            if c.a.get('key_node'):
                return decision('UNKNOWN','プロバイダ管理鍵という申告とカスタマー管理対象key_nodeの登録が併存しています。',fields)
            return decision('PASSED','入力上はプロバイダ管理鍵です。復号経路の実証はCRC-KEY-002で確認します。',['key_management'])
        if not c.a.get('key_node'): return decision('UNKNOWN','カスタマー管理鍵のkey_nodeが未登録です。',fields)
        return _graph_absence(c,c.a['key_node'],fields,{'can_delete','can_disable'},'復号鍵への管理・削除・無効化の実効権限経路があります。データ不変性とは別のリスクです。')
    if kind=='restore':
        method=c.val('restore_method')
        if method is None: return decision('UNKNOWN','復元方式が不明です。',fields)
        if method=='azure_vm_native' and c.a['workload']!='azure_vm':
            return decision('FAILED','標準Azure VM復元は、このワークロードの復元方式として指定できません。',fields)
        if method=='m365_backup' and not is_m365:
            return decision('FAILED','Microsoft 365 Backupと対象ワークロードが一致しません。',fields)
        if method=='aws_backup' and c.a['provider']!='aws':
            return decision('FAILED','AWS Backup方式と対象プロバイダが一致しません。',fields)
        if c.val('restore_supported') is False:
            return decision('FAILED','入力上、対象構成は採用した復元方式で非対応です。',fields)
        groups=[]
        if method in {'azure_vm_native','m365_backup'}:
            source=c.nodes[c.a['production_node']]; target=c.nodes[c.a['recovery_node']]
            st=source['id'] if source['kind']=='tenant' else source.get('tenant')
            tt=target['id'] if target['kind']=='tenant' else target.get('tenant')
            if st is None or tt is None: return decision('UNKNOWN','復元元・先のテナントが不明です。',fields)
            if st!=tt:
                if method=='azure_vm_native':
                    return decision('FAILED','標準Azure VM Cross Subscription Restoreは同一テナント内が条件です。別テナント復元案と一致しません。',fields)
                return decision('UNKNOWN','標準M365 Backupの別テナント復元は、このルール集では対応を確認できません。製品別の対応根拠が必要です。',fields)
            groups=[source.get('evidence',[]),target.get('evidence',[])]
        if c.val('restore_supported') is None: return decision('UNKNOWN','対象/版/鍵/復元先を含めた対応確認が未登録です。',fields)
        if method=='other': return decision('UNKNOWN','other方式の意味は初版ルールでは評価しません。',fields)
        return decision('PASSED','入力上、復元方式の対応確認があり、組込みの既知制約とは矛盾しません。復元成功の判定ではありません。',fields,groups=groups)
    raise RuntimeError('Unimplemented rule kind: '+kind)


def evaluate(model: dict, as_of: date | None = None, max_evidence_age_days: int = 90) -> dict:
    """Review a validated model; PASSED means a modeled condition, never a guarantee."""
    model=deepcopy(validate_model(model))
    if as_of is None: as_of=date.today()
    if type(as_of) is not date: raise ModelError('as_ofはdatetime.dateで指定してください')
    if type(max_evidence_age_days) is not int or not 1<=max_evidence_age_days<=100000:
        raise ModelError('max_evidence_age_daysは1〜100000の整数で指定してください')
    findings=[]
    for scenario in model['scenarios']:
        controlled=control_paths(model,scenario); network=network_paths(model,controlled)
        for assessment in model['assessments']:
            c=Context(model,assessment,scenario,as_of,max_evidence_age_days,controlled,network)
            for rule in RULES:
                d=_rule_decision(c,rule)
                proofs=[c.field_proof(field) for field in d['fields']]
                extra=[c.proof(group) for group in d['groups']]
                levels=[p['level'] for p in proofs+extra]
                # No explicit path means the target itself is a scenario assumption.
                if d['paths']==[[]]: levels=['configuration']
                assurance=min(levels,key=lambda x:RANK[x]) if levels else 'none'
                if d['status']=='PASSED' and any(not p['adequate'] for p in proofs+extra):
                    d['status']='UNKNOWN'; d['message']+=' ただし十分な強度・鮮度の証跡がそろっていません。'
                findings.append({'id':f'{scenario["id"]}/{assessment["id"]}/{rule["id"]}',
                    'scenario_id':scenario['id'],'scenario_name':scenario['name'],
                    'assessment_id':assessment['id'],'assessment_name':assessment['name'],
                    'rule_id':rule['id'],'title':rule['title'],'category':rule['category'],
                    'severity':rule['severity'],'phase':rule['phase'],'status':d['status'],
                    'message':d['message'],'assurance':assurance,'facts':proofs,'path_evidence':extra,
                    'paths':d['paths'],'source_ids':list(rule['source_ids']),
                    'remediation':rule['remediation'],'question':rule['question'],
                    'evidence_note':'証跡メタデータの分類を照合。実ファイルの内容・真正性は未検証。'})
    summary={s:sum(f['status']==s for f in findings) for s in STATUS}
    overall='NEEDS_REMEDIATION' if summary['FAILED'] else ('INSUFFICIENT_EVIDENCE' if summary['UNKNOWN'] else 'MODEL_CHECKS_SATISFIED')
    canonical=json.dumps(model,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return {'report_version':'1.0','tool':'CleanRoomCheck','tool_version':__version__,
            'ruleset_version':RULESET_VERSION,'as_of':as_of.isoformat(),
            'max_evidence_age_days':max_evidence_age_days,'input_sha256':hashlib.sha256(canonical).hexdigest(),
            'project':dict(model['project']),'summary':summary,'overall':overall,
            'disclaimer':DISCLAIMER,'findings':findings,'sources':load_sources(),
            'scenarios':model['scenarios'],'nodes':model['nodes'],'edges':model['edges'],
            'evidence':model['evidence'],
            'assessment_scopes':[{k:a[k] for k in ('id','provider','workload')} for a in model['assessments']]}
