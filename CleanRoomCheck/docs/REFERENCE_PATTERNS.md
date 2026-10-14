# 根拠付き構成パターン集

**対象: 初期の設計比較。実顧客の導入実績や、本ツールで構築・試験した事例ではありません。** 以下は公開された製品仕様・設計指針を基にした構成検討用の整理です。参照確認日: 2026-10-14。製品の版・対象・対応地域・ライセンスを採用時に再確認してください。

## A. Azure: バックアップ保護と復旧先の独立性を分ける

本番サブスクリプションとバックアップ保護のための権限境界を整理し、不変バックアップと破壊的操作の承認分離を組み合わせます。Resource Guardの管理者がバックアップ管理者から独立していることを確認し、保護操作の範囲と不変ロック確定状態を点検します。MicrosoftはResource Guardを別テナントに配置する構成を説明しています。[MS-MUA][MS-IMMUTABLE]

ただし、同じEntraテナントに属するサブスクリプションを分けただけでは、全体管理者の権限昇格を想定した管理境界の独立性にはなりません。顧客の脅威モデルが本番テナント全体管理者の侵害なら、復旧側のID管理を含む独立性と、そこへ移せる復元方式を同時に検討します。[MS-AZURE-ELEVATE]

標準Azure VMのCross Subscription Restoreは同一テナント内という条件があるため、「復旧先を別テナントに変更」しただけの案は完成ではありません。対象製品・方式について別テナント、認証断、暗号化・リージョン等の対応条件を確認します。[MS-VM-RESTORE]

| 設計の要素 | 点検で残す確認 |
|---|---|
| 独立した復旧管理 | 本番SSO、全体管理者、委任、MDM、CI/CDから管理できないか |
| 不変バックアップ | ロック確定、復旧点への適用、保護期限、保持要件 |
| 承認分離 | Resource Guardを含む承認者・権限境界・操作対象 |
| 別境界への復元 | 採用方式の制約・独立した復号・実復元試験 |

関連ルール: CRC-ID-001、CRC-BAK-001/002/005、CRC-KEY-001/002、CRC-REC-001/002。

## B. AWS: 管理アカウント・保管先・復旧アカウントの範囲を明示する

AWS BackupのLogically air-gapped vaultはComplianceモードのVault Lock、AWS RAMによる別アカウントへの共有、Multi-party approvalの経路を説明しています。利用できるリソース・コピー方式・暗号鍵・リージョンなどの制約を個別に確認する構成候補です。[AWS-AIRGAP]

S3 Object LockのGovernance/Compliance、AWS Backup Vault LockのComplianceモードと猶予期間を区別します。保管先やストレージクラスの名称だけで改ざん・削除耐性を合格にしません。S3 Object Lockが暗号鍵の喪失・削除まで保護するわけではない点も別途確認します。[AWS-OBJECT-LOCK][AWS-VAULT-LOCK][AWS-KEY-CAVEAT]

本ツールはAWS Organizationsを自動解析しません。組織管理アカウント、委任管理、ロール引受け、SCP、各保管先を踏まえて解決済みの実効権限を入力します。別アカウントだから必ず独立、別組織なら無条件で復旧できる、といった推論は行いません。

関連ルール: CRC-BAK-001/002/005/006、CRC-KEY-001/002、CRC-REC-001/002。

## C. IRE内部: 管理・検疫・検証後を分ける

Mandiantは、独立した認証や管理端末を用い、復元物を隔離・検証してから復旧に進めるIREの考え方を示しています。これを基に、管理区画、検疫区画、検証後の復旧区画を分け、復元物を最初から信頼しない設計をレビューします。[MANDIANT-IRE]

検証には、マルウェア検査記録、既知正常構成との差分、権限・永続化、資格情報の再発行、ログ保全、業務機能、外部依存先との接続、再接続承認を含めます。これは本ツールのレビュー項目であり、単一のスキャナーがクリーンさを証明するという意味ではありません。

関連ルール: CRC-ID-002/003/004、CRC-NET-001/002/003、CRC-VAL-001〜008。

## D. M365: 業務データの復旧とテナント再構築を分ける

Microsoft 365 BackupはSharePoint、OneDrive、Exchangeのデータ保護・復元を中心とする仕様を公開しています。これをそのままEntra ID・権限・全設定・ドメイン連携を含むテナント全体の再構築と同一視しません。[MS-M365-BACKUP]

設計レビューでは、データ、ID/権限、テナント設定、ドメイン/外部連携の4つに分け、保持される材料、復旧担当者、代替認証、検証手順を整理します。標準M365 Backupの別テナントへの復元可否は本ルール集の自動判定で保証せず、確認待ちとします。選定する製品・方式に応じた検証が必要です。

関連ルール: CRC-M365-001〜004、CRC-REC-001/005。

## 採用判断の位置づけ

本ツールは製品推薦・ライセンス見積・完全なランディングゾーン設計を行いません。構成パターンと脅威モデルを対応させ、不足情報とベンダー確認事項を残すためのものです。「本番が利用不能」と「攻撃者が本番を操作可能」を区別し、復元先の独立性と実際の復旧可否の両方を承認条件にしてください。

## 出典

[MS-AZURE-ELEVATE]: https://learn.microsoft.com/en-us/azure/role-based-access-control/elevate-access-global-admin

[MS-MUA]: https://learn.microsoft.com/en-us/azure/backup/multi-user-authorization

[MS-IMMUTABLE]: https://learn.microsoft.com/en-us/azure/backup/backup-azure-immutable-vault-concept

[MS-VM-RESTORE]: https://learn.microsoft.com/en-us/azure/backup/backup-support-matrix-iaas

[AWS-OBJECT-LOCK]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html

[AWS-KEY-CAVEAT]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html

[AWS-VAULT-LOCK]: https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html

[AWS-AIRGAP]: https://docs.aws.amazon.com/aws-backup/latest/devguide/logicallyairgappedvault.html

[MS-M365-BACKUP]: https://learn.microsoft.com/en-us/microsoft-365/backup/backup-overview?view=o365-worldwide

[MANDIANT-IRE]: https://cloud.google.com/blog/topics/threat-intelligence/isolated-recovery-environments-modern-cyber-resilience

