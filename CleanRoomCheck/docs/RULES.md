# ルール・入力項目一覧

ルールセット: **2026.10-alpha1**。32ルールは業務×侵害シナリオごとに適用されます。規格適合の認証項目ではなく、製品の公式仕様とIRE設計指針を参照した本OSSのレビュー条件です。

## 判定と根拠

`PASSED` は入力条件と必要な証跡メタデータがそろった状態、`FAILED` は入力モデル上の不成立、`UNKNOWN` は不足/未確認、`NOT_APPLICABLE` は対象外です。肯定には各必須条件の証跡が必要です。否定的な入力は未検証でも不備候補として残し、その証跡強度を併記します。

## ルール表

| ID | 点検 | 条件フィールド | 区分 / 重要度 | 出典 |
|---|---|---|---|---|
| CRC-ID-001 | 復旧環境の管理権限・IDの独立性 | `independent_identity`, `control_graph_complete` | design / critical | MS-AZURE-ELEVATE, MANDIANT-IRE |
| CRC-ID-002 | 復旧用管理端末の独立性 | `dedicated_admin_device` | design / high | MANDIANT-IRE |
| CRC-ID-003 | 復旧操作の職務分離・独立承認 | `independent_approval` | design / high | MANDIANT-IRE |
| CRC-ID-004 | 手順書・連絡先への独立したアクセス | `runbook_available` | design / high | MANDIANT-IRE |
| CRC-NET-001 | 侵害起点から復旧側への通信経路 | `network_graph_complete` | design / high | MANDIANT-IRE |
| CRC-NET-002 | 隔離環境の既定拒否 | `network_default_deny` | design / high | MANDIANT-IRE |
| CRC-NET-003 | 検証に必要な外向き通信の限定 | `egress_allowlist` | design / medium | MANDIANT-IRE |
| CRC-BAK-001 | 不変性のモードとロック確定 | `immutable_mode`, `lock_finalized` | design / critical | MS-IMMUTABLE, AWS-OBJECT-LOCK, AWS-VAULT-LOCK |
| CRC-BAK-002 | 実際の復旧点への保護適用と有効期限 | `immutable_applies_to_points`, `protection_until` | design / critical | MS-IMMUTABLE, AWS-OBJECT-LOCK |
| CRC-BAK-003 | 業務要件に対する保持期間 | `retention_days`, `required_retention_days` | design / high | MANDIANT-IRE |
| CRC-BAK-004 | 復旧点の実在と選定根拠の検証 | `recovery_point_exists`, `recovery_point_reviewed` | validation / high | MANDIANT-IRE |
| CRC-BAK-005 | バックアップ破壊的操作の承認分離 | `independent_backup_approval` | design / high | MS-MUA, AWS-AIRGAP |
| CRC-BAK-006 | バックアップ管理面の独立性 | `control_graph_complete` | design / medium | MANDIANT-IRE |
| CRC-KEY-001 | 復号鍵の管理・破壊権限の独立性 | `key_management`, `control_graph_complete` | design / critical | AWS-KEY-CAVEAT, MANDIANT-IRE |
| CRC-KEY-002 | 本番を使わない復号の実証 | `key_usable` | validation / high | AWS-KEY-CAVEAT, MANDIANT-IRE |
| CRC-REC-001 | 復元方式と復元先の対応性 | `restore_method`, `restore_supported` | design / critical | MS-VM-RESTORE, AWS-AIRGAP, MS-M365-BACKUP |
| CRC-REC-002 | 想定侵害条件での復元試験 | `restore_tested` | validation / high | MANDIANT-IRE |
| CRC-REC-003 | RTO目標と実測値の照合 | `rto_hours`, `measured_rto_hours` | validation / high | MANDIANT-IRE |
| CRC-REC-004 | RPO目標と実測損失幅の照合 | `rpo_hours`, `measured_data_loss_hours` | validation / high | MANDIANT-IRE |
| CRC-REC-005 | データ以外の再構築材料の保全 | `control_plane_exported` | design / high | MANDIANT-IRE |
| CRC-M365-001 | M365データ復旧範囲の整理 | `m365_data_covered` | design / high | MS-M365-BACKUP |
| CRC-M365-002 | M365/Entra IDの再構築計画 | `m365_identity_plan` | design / high | MS-M365-BACKUP, MANDIANT-IRE |
| CRC-M365-003 | M365設定の再構築計画 | `m365_config_plan` | design / high | MS-M365-BACKUP, MANDIANT-IRE |
| CRC-M365-004 | M365ドメイン・外部連携計画 | `m365_domain_plan` | design / high | MS-M365-BACKUP, MANDIANT-IRE |
| CRC-VAL-001 | 管理・検疫・検証後の区画分離 | `quarantine_separate` | design / high | MANDIANT-IRE |
| CRC-VAL-002 | 復元物のマルウェア検査記録 | `malware_scan_recorded` | validation / high | MANDIANT-IRE |
| CRC-VAL-003 | 既知正常構成との比較 | `configuration_diff_reviewed` | validation / high | MANDIANT-IRE |
| CRC-VAL-004 | 復元後の権限・永続化確認 | `permissions_reviewed` | validation / high | MANDIANT-IRE |
| CRC-VAL-005 | 復元物に含まれる資格情報の再発行 | `secrets_rotated` | validation / high | MANDIANT-IRE |
| CRC-VAL-006 | ログの不変化と実取得の確認 | `log_immutable`, `log_capture_verified` | validation / high | MANDIANT-IRE |
| CRC-VAL-007 | 本番再接続の承認 | `release_approval` | validation / high | MANDIANT-IRE |
| CRC-VAL-008 | 業務機能・外部依存の検証 | `application_tested`, `external_dependencies_tested` | validation / high | MANDIANT-IRE |

## 全入力項目

| フィールド | 日本語 | 型 / 選択肢 | 肯定に最低限必要な証跡 |
|---|---|---|---|
| `lock_finalized` | 猶予期間終了・不可逆ロックの確定を確認 | boolean + null | configuration |
| `control_graph_complete` | 管理権限グラフの調査範囲を確認済み | boolean + null | configuration |
| `network_graph_complete` | 通信経路グラフの調査範囲を確認済み | boolean + null | configuration |
| `independent_identity` | 復旧側のID・認証管理が独立 | boolean + null | configuration |
| `dedicated_admin_device` | 独立管理の復旧用端末を確保 | boolean + null | configuration |
| `independent_approval` | 復旧操作の承認者・承認経路が独立 | boolean + null | configuration |
| `runbook_available` | 本番IDなしで手順・連絡先を参照可能 | boolean + null | configuration |
| `control_plane_exported` | ID/構成/IaC等の再構築材料を保全 | boolean + null | configuration |
| `network_default_deny` | 復旧環境の通信は既定拒否 | boolean + null | configuration |
| `egress_allowlist` | 外向き通信の許可先を限定 | boolean + null | configuration |
| `immutable_applies_to_points` | 必要な復旧点への不変性適用を確認 | boolean + null | configuration |
| `recovery_point_exists` | 必要な復旧点の実在を確認 | boolean + null | configuration |
| `recovery_point_reviewed` | 復旧点の侵害兆候・選定根拠を検証済み | boolean + null | tested |
| `independent_backup_approval` | バックアップ破壊的操作の承認を分離 | boolean + null | configuration |
| `key_usable` | 独立した復旧経路で復号を検証済み | boolean + null | tested |
| `restore_supported` | 製品/方式の復元先・対象制約を確認済み | boolean + null | configuration |
| `restore_tested` | 想定侵害条件で復元試験を実施済み | boolean + null | tested |
| `m365_data_covered` | M365業務データの復旧範囲を明確化 | boolean + null | configuration |
| `m365_identity_plan` | M365/Entra IDのID・権限再構築計画あり | boolean + null | configuration |
| `m365_config_plan` | M365テナント設定の再構築計画あり | boolean + null | configuration |
| `m365_domain_plan` | M365ドメイン・外部連携の切替計画あり | boolean + null | configuration |
| `quarantine_separate` | 管理区画・検疫区画・検証後区画を分離 | boolean + null | configuration |
| `malware_scan_recorded` | 復元物のマルウェア検査結果を記録 | boolean + null | tested |
| `configuration_diff_reviewed` | 既知正常構成との差分を確認 | boolean + null | tested |
| `permissions_reviewed` | 復元後の権限・永続化設定を確認 | boolean + null | tested |
| `secrets_rotated` | 復元物に含まれる資格情報を再発行 | boolean + null | tested |
| `log_immutable` | ログ保管の不変性を設定 | boolean + null | configuration |
| `log_capture_verified` | ログが実際に取得・保全されることを確認 | boolean + null | tested |
| `release_approval` | 本番再接続の条件と承認記録あり | boolean + null | tested |
| `application_tested` | 業務機能・整合性試験を実施 | boolean + null | tested |
| `external_dependencies_tested` | 外部依存先との復旧接続を試験 | boolean + null | tested |
| `rto_hours` | 目標RTO（時間） | number + null | configuration |
| `measured_rto_hours` | 試験で実測したRTO（時間） | number + null | tested |
| `rpo_hours` | 目標RPO（時間） | number + null | configuration |
| `measured_data_loss_hours` | 選定復旧点による実測データ損失幅（時間） | number + null | tested |
| `retention_days` | バックアップ保持日数 | integer + null | configuration |
| `required_retention_days` | 業務側が定めた必要保持日数 | integer + null | configuration |
| `protection_until` | 必要な復旧点の最も早い不変保護終了日 | date + null | configuration |
| `immutable_mode` | 不変性のモード/ロック確定状態 | none / governance / compliance / azure_locked / azure_unlocked / other_locked + null | configuration |
| `key_management` | 復号鍵の管理方式 | customer / provider + null | configuration |
| `restore_method` | 採用する復元方式 | azure_vm_native / vendor / aws_backup / m365_backup / manual / other + null | configuration |

## 判定上の補足

- 管理/通信経路未検出だけでは成立になりません。対応するグラフの調査範囲確認と証跡が必要です。
- バックアップ管理面、ロック/期限/復旧点、復号鍵は独立して判定します。管理面の到達は不変データの削除成功を意味しません。
- CRC-BAK-001は製品とモードの対応、不可逆確定を照合します。other_lockedは初版ではUNKNOWNです。
- CRC-BAK-003は指定した必要保持日数との大小だけを比較します。要件自体の妥当性を保証しません。
- CRC-REC-001の製品対応は網羅的ではありません。Azure VM標準方式の別テナントは既知制約に不一致、M365標準方式の別テナントは確認待ちです。
- provider-managed鍵という申告とkey_nodeの併存は情報不足扱いです。プロバイダ管理鍵でも復号試験は別に必要です。
- VAL系の記録があることはマルウェア不存在/安全性を保証しません。自動スキャンは行いません。
- 各ルールの修正方針と質問文は実際の診断HTML/質問票CSVに含みます。

## 参照資料

- **MS-AZURE-ELEVATE** — Elevate access to manage all Azure subscriptions and management groups
  https://learn.microsoft.com/en-us/azure/role-based-access-control/elevate-access-global-admin

- **MS-MUA** — Multi-user authorization using Resource Guard
  https://learn.microsoft.com/en-us/azure/backup/multi-user-authorization

- **MS-IMMUTABLE** — Immutable vault for Azure Backup
  https://learn.microsoft.com/en-us/azure/backup/backup-azure-immutable-vault-concept

- **MS-VM-RESTORE** — Support matrix for Azure VM backups
  https://learn.microsoft.com/en-us/azure/backup/backup-support-matrix-iaas

- **AWS-OBJECT-LOCK** — Locking objects with Object Lock
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html

- **AWS-KEY-CAVEAT** — Object Lock considerations
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html

- **AWS-VAULT-LOCK** — AWS Backup Vault Lock
  https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html

- **AWS-AIRGAP** — Logically air-gapped vault
  https://docs.aws.amazon.com/aws-backup/latest/devguide/logicallyairgappedvault.html

- **MS-M365-BACKUP** — Overview of Microsoft 365 Backup
  https://learn.microsoft.com/en-us/microsoft-365/backup/backup-overview?view=o365-worldwide

- **MANDIANT-IRE** — Isolated Recovery Environments: A Critical Layer in Modern Cyber Resilience
  https://cloud.google.com/blog/topics/threat-intelligence/isolated-recovery-environments-modern-cyber-resilience
