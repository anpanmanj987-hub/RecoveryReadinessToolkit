"""Versioned policy catalogue. These are review heuristics, not provider certification."""
from __future__ import annotations
import json
from importlib.resources import files
from .model import FIELDS

RULESET_VERSION='2026.10-alpha1'
TESTED_FIELDS=set('''recovery_point_reviewed key_usable restore_tested malware_scan_recorded configuration_diff_reviewed permissions_reviewed secrets_rotated log_capture_verified release_approval application_tested external_dependencies_tested measured_rto_hours measured_data_loss_hours'''.split())
LABELS={
'lock_finalized':'猶予期間終了・不可逆ロックの確定を確認',
'control_graph_complete':'管理権限グラフの調査範囲を確認済み',
'network_graph_complete':'通信経路グラフの調査範囲を確認済み',
'independent_identity':'復旧側のID・認証管理が独立',
'dedicated_admin_device':'独立管理の復旧用端末を確保',
'independent_approval':'復旧操作の承認者・承認経路が独立',
'runbook_available':'本番IDなしで手順・連絡先を参照可能',
'control_plane_exported':'ID/構成/IaC等の再構築材料を保全',
'network_default_deny':'復旧環境の通信は既定拒否',
'egress_allowlist':'外向き通信の許可先を限定',
'immutable_applies_to_points':'必要な復旧点への不変性適用を確認',
'recovery_point_exists':'必要な復旧点の実在を確認',
'recovery_point_reviewed':'復旧点の侵害兆候・選定根拠を検証済み',
'independent_backup_approval':'バックアップ破壊的操作の承認を分離',
'key_usable':'独立した復旧経路で復号を検証済み',
'restore_supported':'製品/方式の復元先・対象制約を確認済み',
'restore_tested':'想定侵害条件で復元試験を実施済み',
'm365_data_covered':'M365業務データの復旧範囲を明確化',
'm365_identity_plan':'M365/Entra IDのID・権限再構築計画あり',
'm365_config_plan':'M365テナント設定の再構築計画あり',
'm365_domain_plan':'M365ドメイン・外部連携の切替計画あり',
'quarantine_separate':'管理区画・検疫区画・検証後区画を分離',
'malware_scan_recorded':'復元物のマルウェア検査結果を記録',
'configuration_diff_reviewed':'既知正常構成との差分を確認',
'permissions_reviewed':'復元後の権限・永続化設定を確認',
'secrets_rotated':'復元物に含まれる資格情報を再発行',
'log_immutable':'ログ保管の不変性を設定',
'log_capture_verified':'ログが実際に取得・保全されることを確認',
'release_approval':'本番再接続の条件と承認記録あり',
'application_tested':'業務機能・整合性試験を実施',
'external_dependencies_tested':'外部依存先との復旧接続を試験',
'protection_until':'必要な復旧点の最も早い不変保護終了日',
'retention_days':'バックアップ保持日数',
'required_retention_days':'業務側が定めた必要保持日数',
'key_management':'復号鍵の管理方式',
'immutable_mode':'不変性のモード/ロック確定状態',
'restore_method':'採用する復元方式',
'rto_hours':'目標RTO（時間）',
'measured_rto_hours':'試験で実測したRTO（時間）',
'rpo_hours':'目標RPO（時間）',
'measured_data_loss_hours':'選定復旧点による実測データ損失幅（時間）',
}


def rule(rid,title,fields,kind='all_true',severity='high',phase='design',sources=None,remediation='',question=''):
    return {'id':rid,'title':title,'fields':fields.split(), 'kind':kind,'category':rid.split('-')[1],
            'severity':severity,'phase':phase,'source_ids':sources or ['MANDIANT-IRE'],
            'remediation':remediation or f'「{title}」について設計/試験を見直し、項目単位の証跡を登録してください。',
            'question':question or f'「{title}」を、対象範囲・構成/試験日・根拠資料を含めて説明できますか？'}

RULES=[
rule('CRC-ID-001','復旧環境の管理権限・IDの独立性','independent_identity control_graph_complete','identity', 'critical',sources=['MS-AZURE-ELEVATE','MANDIANT-IRE'],remediation='本番から復旧側へ至る実効管理権限を分離。テナント分離と復元方式の対応性をセットで確認。',question='本番管理者、委任、SSO、共通CI/CD、MDMから復旧側を管理できる経路は残りませんか？'),
rule('CRC-ID-002','復旧用管理端末の独立性','dedicated_admin_device'),
rule('CRC-ID-003','復旧操作の職務分離・独立承認','independent_approval'),
rule('CRC-ID-004','手順書・連絡先への独立したアクセス','runbook_available'),
rule('CRC-NET-001','侵害起点から復旧側への通信経路','network_graph_complete','network',question='選択シナリオの侵害起点から復旧側まで、実効的な許可通信は存在しますか？'),
rule('CRC-NET-002','隔離環境の既定拒否','network_default_deny'),
rule('CRC-NET-003','検証に必要な外向き通信の限定','egress_allowlist',severity='medium'),
rule('CRC-BAK-001','不変性のモードとロック確定','immutable_mode lock_finalized','lock','critical',sources=['MS-IMMUTABLE','AWS-OBJECT-LOCK','AWS-VAULT-LOCK'],remediation='解除可能なモードと確定済みロックを区別。対象サービス・状態を確認し、不可逆操作は人が承認して実施。',question='保管先の正確な製品、ロックモード、猶予期間終了、対象復旧点への適用を示せますか？'),
rule('CRC-BAK-002','実際の復旧点への保護適用と有効期限','immutable_applies_to_points protection_until','protection','critical',sources=['MS-IMMUTABLE','AWS-OBJECT-LOCK']),
rule('CRC-BAK-003','業務要件に対する保持期間','retention_days required_retention_days','retention',sources=['MANDIANT-IRE'],remediation='一律の日数で安全とせず、調査・復旧の想定に基づく必要保持日数を業務側で決定。'),
rule('CRC-BAK-004','復旧点の実在と選定根拠の検証','recovery_point_exists recovery_point_reviewed',phase='validation',remediation='必要な復旧点の実在と選定根拠を確認。検証済みでもマルウェア不存在の証明とは扱わない。'),
rule('CRC-BAK-005','バックアップ破壊的操作の承認分離','independent_backup_approval',sources=['MS-MUA','AWS-AIRGAP']),
rule('CRC-BAK-006','バックアップ管理面の独立性','control_graph_complete','backup',severity='medium',remediation='管理面の共有範囲と変更可能操作を確認。管理面への到達は、不変復旧点の削除成功とは別の評価。'),
rule('CRC-KEY-001','復号鍵の管理・破壊権限の独立性','key_management control_graph_complete','key','critical',sources=['AWS-KEY-CAVEAT','MANDIANT-IRE'],remediation='復号鍵の管理・無効化・削除の実効権限を分離し、鍵を使える復旧経路も別途試験。'),
rule('CRC-KEY-002','本番を使わない復号の実証','key_usable',phase='validation',sources=['AWS-KEY-CAVEAT','MANDIANT-IRE']),
rule('CRC-REC-001','復元方式と復元先の対応性','restore_method restore_supported','restore','critical',sources=['MS-VM-RESTORE','AWS-AIRGAP','MS-M365-BACKUP'],remediation='対象製品・版・ワークロード・リージョン・鍵・テナント/アカウント制約を裏付ける資料を確認。',question='想定する復元元/先と認証断の条件で、その製品・版・ワークロードは復元可能ですか？'),
rule('CRC-REC-002','想定侵害条件での復元試験','restore_tested',phase='validation'),
rule('CRC-REC-003','RTO目標と実測値の照合','rto_hours measured_rto_hours','rto',phase='validation'),
rule('CRC-REC-004','RPO目標と実測損失幅の照合','rpo_hours measured_data_loss_hours','rpo',phase='validation'),
rule('CRC-REC-005','データ以外の再構築材料の保全','control_plane_exported'),
rule('CRC-M365-001','M365データ復旧範囲の整理','m365_data_covered',sources=['MS-M365-BACKUP']),
rule('CRC-M365-002','M365/Entra IDの再構築計画','m365_identity_plan',sources=['MS-M365-BACKUP','MANDIANT-IRE']),
rule('CRC-M365-003','M365設定の再構築計画','m365_config_plan',sources=['MS-M365-BACKUP','MANDIANT-IRE']),
rule('CRC-M365-004','M365ドメイン・外部連携計画','m365_domain_plan',sources=['MS-M365-BACKUP','MANDIANT-IRE']),
rule('CRC-VAL-001','管理・検疫・検証後の区画分離','quarantine_separate'),
rule('CRC-VAL-002','復元物のマルウェア検査記録','malware_scan_recorded',phase='validation'),
rule('CRC-VAL-003','既知正常構成との比較','configuration_diff_reviewed',phase='validation'),
rule('CRC-VAL-004','復元後の権限・永続化確認','permissions_reviewed',phase='validation'),
rule('CRC-VAL-005','復元物に含まれる資格情報の再発行','secrets_rotated',phase='validation'),
rule('CRC-VAL-006','ログの不変化と実取得の確認','log_immutable log_capture_verified',phase='validation'),
rule('CRC-VAL-007','本番再接続の承認','release_approval',phase='validation'),
rule('CRC-VAL-008','業務機能・外部依存の検証','application_tested external_dependencies_tested',phase='validation'),
]


def load_sources():
    return json.loads(files('cleanroomcheck').joinpath('data','sources.json').read_text(encoding='utf-8'))


def field_catalog():
    return {field:{'label':LABELS[field],'type':kind if isinstance(kind,str) else 'enum',
                   'options':list(kind) if isinstance(kind,tuple) else [],
                   'minimum_evidence':'tested' if field in TESTED_FIELDS else 'configuration'} for field,kind in FIELDS.items()}
