# CleanRoomCheck alpha — design

## Intent
ユーザー承認済みの企画を、クラウドテナント侵害を想定したクリーン環境の設計レビューOSSとして実装する。実顧客データは使用しない。実クラウドを変更しない。製品名の仮称はCleanRoomCheck、バージョンは0.1.0a1。

## Scope and constraints
- Python >=3.10。JSON/CSV/CLI/HTML/ローカルWeb UIは標準ライブラリのみ。YAMLは任意のPyYAML依存。
- 各社の入力を別ファイルに保持する。サーバは127.0.0.1限定でセッション中だけ動作、外部送信・クラウドAPI呼出・入力永続化なし。
- 入力はproject、evidence、nodes、edges、scenarios、assessments。nodesは資産、edgesは明示的な管理/破壊/通信/依存関係。assessmentsは1業務の本番・復旧先・保管先・鍵と構成事実。
- エッジのcontrolsだけが管理権限を伝播する。network_reach、depends_on、can_delete、can_disableは管理権限を伝播しない。Azure Global Administratorのシナリオでは、当該tenantから同tenantのsubscriptionへの管理権限昇格を限定的に推論。AWS Organizationsの権限は推論しない。
- 判定はPASSED/FAILED/UNKNOWN/NOT_APPLICABLE。PASSEDは入力モデルと指定証跡メタデータ上の成立であり安全性保証ではない。欠落・古い/未来の証跡・自己申告は肯定判定を許可しない。既定証跡許容期間90日は変更可能な本OSSの方針、業界基準ではない。
- 複数条件は各条件の証跡を要求。負の入力は証跡がなくても設計不備候補としてFAILEDを出すが、その根拠強度を表示。証跡の実ファイル/署名/真正性は検証しない。
- バックアップ管理面の侵害をデータ消失と同一視しない。ロック状態、実際の復旧点、期限、保管期間、復号、復元方式、検証を分離する。
- 初版は設定収集器、IaCデプロイ、復元実行、マルウェア検出エンジン、BreakGlassMapとの実スキーマ互換を実装しない。
- 公式出典と取得日をルール/構成パターンに付与する。構築例は参照パターン、導入実績ではない。

## Deliverables
根拠付き診断JSON/HTML、ベンダー質問票CSV、検証チェックCSV、構成変更比較HTML/JSON、出典集、データモデルとルール仕様、架空Azureの不備/改善案/AWS/M365/未入力サンプル、ローカル入力フォーム、単体/統合/UIテスト、CI定義、MITライセンス、公開手順、ZIPとwheel。

## Safety and robustness
厳密な型・ID・参照検証、重複キー拒否、入力サイズ/深さ/件数制限、YAML safe load/alias拒否、HTML escapingとCSP、CSV数式注入対策、ローカルUI Host/Origin/token検証、入力ファイル上書き拒否。任意コマンドやルール式の実行はしない。

## Verification
テスト先行。権限の誤伝播、同一tenant、鍵喪失可能性、ロック期限、未設定、RTO/RPO、証跡鮮度、自己申告、XSS、CSV/YAML、不正参照、比較時の対象削除をテスト。ランダムなグラフを独立した到達性計算と比較する。ブラウザとwheelを実行して納品前に確認する。実クラウド検証と第三者レビュー未実施を明記する。
