"""Regenerate synthetic public examples; never load customer data."""
from pathlib import Path
import copy
import json
from tests.helpers import base_model, fact, edge, TESTED_FIELDS
from cleanroomcheck.model import FIELDS, validate_model

root=Path(__file__).resolve().parents[1]

def save(name,model):
    validate_model(model)
    text=json.dumps(model,ensure_ascii=False,indent=2)+'\n'
    for directory in [root/'examples',root/'cleanroomcheck/data/examples']:
        (directory/(name+'.json')).write_text(text,encoding='utf-8')

# All evidence and assertions are synthetic examples; tested labels are never real tests.
m=base_model(); m['project']['name']='架空金融グループ / クリーン環境検討'
m['project']['description']='公開デモ用の架空構成。実顧客の環境や製品の導入実績ではない。'
m['evidence'][0]['reference']='仮定: 設計レビュー資料 rev1（実設定の取得ではない）'
m['evidence'][0]['note']='デモのためconfigurationとして登録。実設定を取得した証跡ではない。'
m['evidence'][1]['reference']='仮定: 試験記録の記入例（実機試験は未実施）'
m['evidence'][1]['note']='デモスキーマ説明用。実施済み試験として顧客に提示しない。'
for field in TESTED_FIELDS: fact(m,field,None,[])
m['nodes'] += [
 {'id':'backup-admin','label':'バックアップ管理者','kind':'identity','provider':'azure','plane':'backup','evidence':['cfg']},
 {'id':'shared-pipeline','label':'共通CI/CD','kind':'pipeline','provider':'azure','plane':'shared','evidence':['cfg']},
]
m['scenarios'] += [
 {'id':'backup-admin-takeover','name':'バックアップ管理者侵害','compromised':['backup-admin']},
 {'id':'pipeline-takeover','name':'共通CI/CD侵害','compromised':['shared-pipeline']},
]
m['nodes'][3]['tenant']='prod-tenant'
fact(m,'restore_method','azure_vm_native')
for key in ['independent_identity','dedicated_admin_device','independent_approval','runbook_available','network_default_deny','egress_allowlist','independent_backup_approval','control_plane_exported']:
    fact(m,key,False)
fact(m,'immutable_mode','azure_unlocked');fact(m,'lock_finalized',False)
fact(m,'retention_days',10);fact(m,'required_retention_days',90)
edge(m,'prod-sub','key','can_disable');edge(m,'prod-sub','rec-sub','network_reach')
edge(m,'backup-admin','vault');edge(m,'backup-admin','key','can_delete')
edge(m,'shared-pipeline','rec-sub');edge(m,'shared-pipeline','key','can_disable')
save('azure-risky',m)
a=copy.deepcopy(m)
a['nodes'][3]['tenant']='rec-tenant'
a['edges']=[]
for key in ['independent_identity','dedicated_admin_device','independent_approval','runbook_available','network_default_deny','egress_allowlist','independent_backup_approval','control_plane_exported']:
    fact(a,key,True)
fact(a,'restore_method','vendor');fact(a,'restore_supported',None,[])
a['assessments'][0]['note']='製品未選定の設計案。別テナントへの対応性はベンダー確認待ち。設定・試験は未実施。'
fact(a,'immutable_mode','azure_locked');fact(a,'lock_finalized',True);fact(a,'retention_days',120)
save('azure-improved',a)

aws=base_model(); aws['project']['id']='fictional-aws';aws['project']['name']='架空AWS / 分離保管と復旧経路'
aws['nodes']=[
 {'id':'prod','label':'本番AWSアカウント','kind':'account','provider':'aws','plane':'production','evidence':['cfg']},
 {'id':'rec','label':'独立復旧アカウント','kind':'account','provider':'aws','plane':'recovery','evidence':['cfg']},
 {'id':'vault','label':'Logically air-gapped vault想定','kind':'backup','provider':'aws','plane':'backup','evidence':['cfg']},
 {'id':'logs','label':'検証ログ','kind':'log_store','provider':'aws','plane':'recovery','evidence':['cfg']},
 {'id':'organization-admin','label':'Organizations管理面','kind':'identity','provider':'aws','plane':'shared','evidence':['cfg']},
]
aws['scenarios']=[{'id':'account-takeover','name':'本番アカウント侵害','compromised':['prod']},
                  {'id':'organization-takeover','name':'組織管理面侵害（権限未調査）','compromised':['organization-admin']}]
ass=aws['assessments'][0];ass.update(provider='aws',workload='aws_ec2',production_node='prod',recovery_node='rec',key_node=None)
for key in TESTED_FIELDS: fact(aws,key,None,[])
fact(aws,'immutable_mode','compliance');fact(aws,'key_management','provider');fact(aws,'restore_method','aws_backup')
fact(aws,'restore_supported',None,[]);fact(aws,'control_graph_complete',None,[])
ass['note']='AWS RAM/承認方式/対象リソース/鍵の条件は未確認。Organizationsの管理権限を自動で全権限と推論しない。'
save('aws',aws)

m365=base_model();m365['project']['id']='fictional-m365';m365['project']['name']='架空M365 / データ復旧とテナント再構築'
a=m365['assessments'][0];a.update(provider='m365',workload='m365',name='OA基盤',production_node='prod-tenant',recovery_node='rec-tenant')
for key in TESTED_FIELDS: fact(m365,key,None,[])
fact(m365,'restore_method','m365_backup')
for key in ['m365_identity_plan','m365_config_plan','m365_domain_plan']:fact(m365,key,None,[])
a['note']='データ保護とテナント全体の再構築を分けて検討するための例。別テナントへの標準M365 Backup復元を対応済みとは仮定しない。'
save('m365',m365)

blank={'schema_version':'1.0','project':{'id':'your-project','name':'新規レビュー','demo':False},'evidence':[],
'nodes':[{'id':'production','label':'本番','kind':'workload','provider':'generic','plane':'production'},
{'id':'recovery','label':'復旧先','kind':'recovery','provider':'generic','plane':'recovery'},
{'id':'backup','label':'バックアップ保管先','kind':'backup','provider':'generic','plane':'backup'}],
'edges':[],'scenarios':[{'id':'production-compromise','name':'本番管理面侵害','compromised':['production']}],
'assessments':[{'id':'workload','name':'対象業務','provider':'generic','workload':'other','production_node':'production','recovery_node':'recovery','backup_node':'backup','facts':{f:{'value':None,'evidence':[]} for f in FIELDS}}]}
save('blank',blank)
