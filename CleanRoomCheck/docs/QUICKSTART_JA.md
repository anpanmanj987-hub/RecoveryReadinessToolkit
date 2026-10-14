# CleanRoomCheck 操作ガイド

## 1. 架空デモを読む

Python 3.10以上を用意し、ZIPを解凍します。Windowsのターミナル、macOS/LinuxのターミナルでREADMEのあるフォルダーへ移動します。macOS/Linuxで `python` がない場合は `python3` に置き換えてください。

```bash
python -m cleanroomcheck demo --out demo-output
```

`demo-output/comparison.html` をブラウザで開きます。最初から生成したデモは配布ZIPの `demo/comparison.html` にもあります。デモ閲覧だけならPythonは不要です。HTMLは外部JavaScript・外部フォントを読み込みません。

Azure例は「不備のある構成」と「改善設計案」の比較であり、実環境での構築・試験結果ではありません。件数は業務×想定侵害シナリオ×ルール単位です。

## 2. ローカル画面で編集する

```bash
python -m cleanroomcheck serve --open-browser
```

Windowsは `launch_windows.cmd` からも起動できます。表示されない場合はターミナルに出る `http://127.0.0.1:8765/` を開きます。ポートが使用中なら `--port 8766` を追加します。許可された端末・ブラウザで使用し、組織のブラウザ制限を解除して利用することは推奨しません。

1. 「空の構成」または架空テンプレートを選んで読み込みます。
2. プロジェクト名・評価日・証跡の許容日数を確認します。
3. 業務を選択し、各項目を成立／不成立／未確認で記入します。未知は空欄のままにします。
4. 証跡IDを各項目に対応付けます。証跡の追加、資産・権限・シナリオの編集は「高度な編集」のJSONで行います。
5. 高度な編集後は「JSONを検証・反映」を押します。未反映の編集がある間は点検できません。
6. 「点検する」を押し、不成立と情報不足の根拠を確認します。
7. 構成JSON・診断HTML・質問票・検証計画を必要に応じ保存します。

入力はメモリー上だけで扱います。変更後の古い結果は無効になります。画面を閉じる前に構成JSONを明示的に保存してください。ローカルUIをリバースプロキシ経由などで外部公開しないでください。

## 3. 会社ごとの構成を作る

```bash
python -m cleanroomcheck init --template blank --out company-a.json
python -m cleanroomcheck validate company-a.json
python -m cleanroomcheck check company-a.json --out company-a-review --as-of 2026-10-14
```

会社ごとに独立したJSONを作ります。`project.demo` を false にすると架空デモの表示が外れますが、それだけで実測になるわけではありません。想定・設計案であることはプロジェクトの説明と証跡の注記に明記してください。

`blank` は入力形式の出発点です。初期資産名・ID・プロバイダ・業務を実際の対象に置き換えてください。JSONの最小例と各フィールドは `MODEL.md` を参照します。

点検コマンドは情報不足を含むと終了コード1になります。レポートはその場合でも生成されます。出力先は存在しない新しいフォルダーを指定してください。既存資料は上書きしません。

## 4. 最初のヒアリングで集めるもの

| 情報 | 具体的な質問 |
|---|---|
| 想定侵害 | 業務管理者、Entra全体管理者、バックアップ管理者、共通端末のどれが支配される想定か |
| 管理境界 | 復旧環境を変更できるID・委任・CI/CD・MDM・承認経路は何か |
| 通信 | 各侵害起点と管理対象から復旧側に到達可能な実効通信は何か |
| 保管と鍵 | 不変モード、確定状態、復旧点別の保護、鍵削除/無効化の実効権限は何か |
| 復元先 | 製品・版・ワークロード・暗号鍵・復元先に関する制約を誰が確認したか |
| 復旧試験 | 本番IDを使用しない復号・復元試験、RTO/RPO、業務確認はいつ実施したか |
| 再接続 | 検疫、構成差分、資格情報、ログ、再接続承認の証跡はあるか |

資料の実体を人が照合したうえで参照情報を入力します。本ツールは添付資料の内容や真正性を自動で審査しません。

## 5. Excelで事実欄を整理する

```bash
python -m cleanroomcheck csv-export company-a.json --out company-a-csv
python -m cleanroomcheck check company-a-csv --out company-a-csv-review
```

`structure.json` は資産・権限・証跡の定義、`facts.csv` は業務ごとの事実です。`value_json` の文字列にはJSONの引用符が必要です（例: `"vendor"`）。真偽値は小文字の `true` / `false`、未確認は `null` です。CSVだけからテナント構成を推測する機能はありません。

## 6. 比較する

```bash
python -m cleanroomcheck compare company-a-before.json company-a-after.json --out company-a-comparison --as-of 2026-10-14
```

比較時は同一project.id・同一侵害シナリオを維持します。対象の削除・シナリオ変更・判定の未確認化は改善件数に入りません。同じIDの意味そのものを書き換えると意味的な同一性を判別できないため、IDは安定させ、構成変更の理由を人がレビューしてください。

## よくある状況

- 「情報不足」ばかり出る: 未入力、証跡の紐付け忘れ、自己申告のみ、古い証跡、実施していない試験を確認します。
- 「成立」にならないため証跡をtestedに変更する: 不適切です。実際に試験していなければ未確認のまま残します。
- 2MiBを超える: 巨大な証跡やバックアップデータを埋め込まず、レビューに必要な構成情報と参照だけを登録します。
- YAMLを使う: `python -m pip install ".[yaml]"` で任意依存を導入します。初版はJSONから始めることを推奨します。
- Pythonなしで閲覧したい: 配布済み `demo/` のHTMLを開きます。自社入力の評価にはPythonが必要です。
