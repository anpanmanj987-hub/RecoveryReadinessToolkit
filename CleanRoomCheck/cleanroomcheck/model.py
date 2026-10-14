"""Strict normalized model. No silent coercion, unknown keys or executable rules."""
from __future__ import annotations
import math
import re
from datetime import date
from typing import Any

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 32
MAX_ITEMS = 50000
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$')
PROVIDERS = {'azure', 'aws', 'm365', 'generic'}
KINDS = {'tenant', 'account', 'subscription', 'identity', 'device', 'pipeline',
         'recovery', 'workload', 'backup', 'key', 'network', 'document', 'log_store', 'approval'}
RELATIONS = {'controls', 'can_delete', 'can_disable', 'network_reach', 'depends_on'}
EVIDENCE_TYPES = {'self_reported', 'configuration', 'tested'}
BOOL_FIELDS = '''lock_finalized control_graph_complete network_graph_complete independent_identity dedicated_admin_device independent_approval runbook_available control_plane_exported network_default_deny egress_allowlist immutable_applies_to_points recovery_point_exists recovery_point_reviewed independent_backup_approval key_usable restore_supported restore_tested m365_data_covered m365_identity_plan m365_config_plan m365_domain_plan quarantine_separate malware_scan_recorded configuration_diff_reviewed permissions_reviewed secrets_rotated log_immutable log_capture_verified release_approval application_tested external_dependencies_tested'''.split()
FIELDS: dict[str, Any] = {k: 'boolean' for k in BOOL_FIELDS}
FIELDS.update({k: 'number' for k in ('rto_hours', 'measured_rto_hours', 'rpo_hours', 'measured_data_loss_hours')})
FIELDS.update({k: 'integer' for k in ('retention_days', 'required_retention_days')})
FIELDS.update({
    'protection_until': 'date',
    'immutable_mode': ('none', 'governance', 'compliance', 'azure_locked', 'azure_unlocked', 'other_locked'),
    'key_management': ('customer', 'provider'),
    'restore_method': ('azure_vm_native', 'vendor', 'aws_backup', 'm365_backup', 'manual', 'other'),
})

class ModelError(ValueError):
    """An input cannot be safely or unambiguously evaluated."""


def parse_date(value: Any, path: str = 'date') -> date:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ModelError(f'{path}: YYYY-MM-DD形式の日付が必要です')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ModelError(f'{path}: 存在する日付を指定してください') from exc


def check_budget(data: Any) -> None:
    stack = [(data, 0)]; items = 0
    while stack:
        value, depth = stack.pop(); items += 1
        if depth > MAX_DEPTH or items > MAX_ITEMS:
            raise ModelError('入力の深さまたは要素数が制限を超えています')
        if isinstance(value, dict):
            if any(not isinstance(k, str) for k in value):
                raise ModelError('すべてのオブジェクトキーは文字列で指定してください')
            if any(0xD800 <= ord(c) <= 0xDFFF for key in value for c in key):
                raise ModelError('単独のUnicodeサロゲートは使用できません')
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            stack.extend((v, depth + 1) for v in value)
        elif isinstance(value, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ModelError('単独のUnicodeサロゲートは使用できません')
        elif isinstance(value, float) and not math.isfinite(value):
            raise ModelError('NaN/Infinityは使用できません')
        elif not (value is None or isinstance(value, (str, int, float, bool))):
            raise ModelError('入力にはJSON互換の値のみ使用できます')


def obj(value: Any, allowed: set[str], required: set[str], path: str) -> dict:
    if not isinstance(value, dict):
        raise ModelError(f'{path}: オブジェクトが必要です')
    unknown, missing = set(value) - allowed, required - set(value)
    if unknown: raise ModelError(f'{path}: 未対応の項目 {", ".join(sorted(unknown))}')
    if missing: raise ModelError(f'{path}: 必須項目がありません {", ".join(sorted(missing))}')
    return value


def text(value: Any, path: str, max_length: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ModelError(f'{path}: 1〜{max_length}文字の文字列が必要です')
    if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
        raise ModelError(f'{path}: 制御文字は使用できません')
    return value


def identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ModelError(f'{path}: IDは英数字で始まる80文字以内の英数字・_.:-です')
    return value


def choices(value: Any, options: Any, path: str) -> None:
    if not isinstance(value, str) or value not in options:
        raise ModelError(f'{path}: {", ".join(sorted(options))} のいずれかを指定してください')


def id_list(value: Any, path: str, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= 500:
        raise ModelError(f'{path}: {minimum}〜500件のID配列が必要です')
    for item in value: identifier(item, path)
    if len(set(value)) != len(value): raise ModelError(f'{path}: 重複IDがあります')
    return value


def fact_value(field: str, value: Any, path: str) -> None:
    if value is None: return
    kind = FIELDS[field]
    if kind == 'boolean':
        if type(value) is not bool: raise ModelError(f'{path}: true/false/nullを指定してください')
    elif kind in ('integer', 'number'):
        ok = type(value) is int if kind == 'integer' else type(value) in (int, float)
        if not ok or not 0 <= value <= 1000000 or not math.isfinite(value):
            raise ModelError(f'{path}: 0〜1000000の{kind}を指定してください（boolは不可）')
    elif kind == 'date': parse_date(value, path)
    else: choices(value, kind, path)


def validate_model(data: Any) -> dict:
    """Validate in place without changing the model; return the same dictionary."""
    check_budget(data)
    keys = {'schema_version', 'project', 'evidence', 'nodes', 'edges', 'scenarios', 'assessments'}
    obj(data, keys, keys, '$')
    if data['schema_version'] != '1.0': raise ModelError('schema_version: 対応版は1.0です')
    p = obj(data['project'], {'id','name','description','demo'}, {'id','name','demo'}, 'project')
    identifier(p['id'],'project.id'); text(p['name'],'project.name',200)
    if type(p['demo']) is not bool: raise ModelError('project.demo: boolが必要です')
    if 'description' in p: text(p['description'],'project.description')
    limits = {'evidence': (0,2000), 'nodes': (1,500), 'edges': (0,2000), 'scenarios': (1,16), 'assessments': (1,50)}
    indexes = {}
    for section, (low, high) in limits.items():
        entries = data[section]
        if not isinstance(entries, list) or not low <= len(entries) <= high:
            raise ModelError(f'{section}: {low}〜{high}件が必要です')
        ids = {}
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict): raise ModelError(f'{section}[{i}]: オブジェクトが必要です')
            item_id = identifier(entry.get('id'), f'{section}[{i}].id')
            if item_id in ids: raise ModelError(f'{section}: 重複ID {item_id}')
            ids[item_id] = entry
        indexes[section] = ids
    if len(data['assessments']) * len(data['scenarios']) > 200:
        raise ModelError('assessment×scenarioは200組以下にしてください')
    evidence, nodes = indexes['evidence'], indexes['nodes']
    def refs(ids, path):
        for ref in id_list(ids, path):
            if ref not in evidence: raise ModelError(f'{path}: 存在しない証跡ID {ref}')
    def node_ref(ref, path, kinds=None):
        identifier(ref, path)
        if ref not in nodes: raise ModelError(f'{path}: 存在しないnode {ref}')
        if kinds and nodes[ref].get('kind') not in kinds:
            raise ModelError(f'{path}: nodeの種類が不適切です')
    for item in data['evidence']:
        path=f'evidence.{item["id"]}'
        obj(item, {'id','type','collected_at','reference','note'}, {'id','type','collected_at','reference'}, path)
        choices(item['type'], EVIDENCE_TYPES, path+'.type')
        parse_date(item['collected_at'], path+'.collected_at'); text(item['reference'], path+'.reference',500)
        if 'note' in item: text(item['note'],path+'.note')
    for item in data['nodes']:
        path=f'nodes.{item["id"]}'
        obj(item, {'id','label','kind','provider','plane','tenant','evidence','note'}, {'id','label','kind','provider','plane'}, path)
        text(item['label'],path+'.label',200); choices(item['kind'], KINDS,path+'.kind')
        choices(item['provider'],PROVIDERS,path+'.provider')
        choices(item['plane'],{'production','backup','recovery','shared'},path+'.plane')
        refs(item.get('evidence',[]),path+'.evidence')
        if 'note' in item: text(item['note'],path+'.note')
    for item in data['nodes']:
        if 'tenant' in item:
            node_ref(item['tenant'], f'nodes.{item["id"]}.tenant', {'tenant'})
            if item['tenant']==item['id']: raise ModelError('tenantの自己参照はできません')
            if item['provider'] not in {'azure','m365'}: raise ModelError('tenant属性はAzure/M365 node専用です')
    for item in data['edges']:
        path=f'edges.{item["id"]}'
        obj(item, {'id','source','target','relation','evidence','note'}, {'id','source','target','relation'}, path)
        node_ref(item['source'],path+'.source'); node_ref(item['target'],path+'.target')
        choices(item['relation'],RELATIONS,path+'.relation'); refs(item.get('evidence',[]),path+'.evidence')
        if 'note' in item: text(item['note'],path+'.note')
    for item in data['scenarios']:
        path=f'scenarios.{item["id"]}'
        obj(item, {'id','name','compromised','azure_global_admin_tenants','note'}, {'id','name','compromised'}, path)
        text(item['name'],path+'.name',200)
        for ref in id_list(item['compromised'],path+'.compromised',1): node_ref(ref,path+'.compromised')
        for ref in id_list(item.get('azure_global_admin_tenants',[]),path+'.azure_global_admin_tenants'):
            node_ref(ref,path+'.azure_global_admin_tenants',{'tenant'})
            if ref not in item['compromised'] or nodes[ref]['provider'] != 'azure':
                raise ModelError(f'{path}: 全体管理者推論は侵害対象のAzure tenantに限ります')
        if 'note' in item: text(item['note'],path+'.note')
    for item in data['assessments']:
        path=f'assessments.{item["id"]}'
        required={'id','name','provider','workload','production_node','recovery_node','backup_node','facts'}
        obj(item, required|{'key_node','log_node','note'},required,path)
        text(item['name'],path+'.name',200); choices(item['provider'],PROVIDERS,path+'.provider')
        choices(item['workload'], {'azure_vm','aws_ec2','m365','other'},path+'.workload')
        expected={'azure_vm':'azure','aws_ec2':'aws','m365':'m365'}.get(item['workload'])
        if expected and item['provider']!=expected: raise ModelError(path+': provider/workloadが矛盾しています')
        for key in ['production_node','recovery_node']:
            node_ref(item[key],path+'.'+key,{'tenant','subscription','account','recovery','workload'})
        node_ref(item['backup_node'],path+'.backup_node',{'backup'})
        for key,kind in [('key_node','key'),('log_node','log_store')]:
            if key in item and item[key] is not None: node_ref(item[key],path+'.'+key,{kind})
        obj(item['facts'],set(FIELDS),set(),path+'.facts')
        for field, claim in item['facts'].items():
            cp=path+'.facts.'+field
            obj(claim, {'value','evidence'}, {'value'}, cp)
            fact_value(field,claim['value'],cp+'.value'); refs(claim.get('evidence',[]),cp+'.evidence')
        if 'note' in item: text(item['note'],path+'.note')
    return data
