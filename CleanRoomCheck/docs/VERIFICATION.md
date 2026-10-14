# Verification record — 0.1.0a1

**実施日: 2026-10-14 / Linux x86_64 / Python 3.13.5 / local alpha build**

後続のWindows・実ブラウザ検証と修正記録は [REVIEW-2026-10-14.md](REVIEW-2026-10-14.md) を参照してください。以下は元のLinux検証時点の記録です。

## 実施した確認

| 確認 | 結果 | 範囲 |
|---|---|---|
| Python自動テスト | **95テスト成功、失敗0** | 型・参照・入力制限、ルール、証跡、比較、CLI、HTML/CSV、ローカルHTTP |
| グラフの独立実装との比較 | **500生成ケース一致** | 管理権限の到達可能性。上の95テストの一部 |
| 32ルールの必須条件欠落 | **32サブケース成功** | 必須条件を消すと成立にしない。95テストに内包 |
| コアPythonステートメントカバレッジ | **90%（丸め値）** | 836 statements / 87 missed。外部起動したCLIとブラウザ試験はカバレッジ集計外 |
| ブラウザのオフラインDOM確認 | **11項目成功** | 入力、再点検、残存UNKNOWN、JSON重複、自己申告、古い応答の破棄、HTML、390px幅 |
| JavaScript構文確認 | 成功 | `node --check cleanroomcheck/web/app.js` |
| Pythonバイトコード確認 | 成功 | `python -m compileall -q cleanroomcheck tests` |
| JSON Schema整合 | 5テンプレート成功 | draft2020-12 + format checker。意味的検証は別途Pythonで実施 |
| wheelビルド・インストール | 成功 | ローカルソースから依存解決・外部アクセスなしでビルド/インストール |
| ソース外・追加site-packagesなしの動作 | 成功 | インストール先のみPYTHONPATHに指定し、`python -S`でバージョン/デモ/HTTPを実行 |
| インストール済みwheelのHTTP | 成功 | HTML、JS、5テンプレート、改善例の評価45/0/39/12 |
| ソース/wheelの再現性 | 同一 | before/after report.jsonのバイト列を比較 |

記録ファイルは `docs/verification/`、表示例は `docs/screenshots/` にあります。テスト数はテストメソッド数であり、95件の攻撃・95種類のクラウド構成を実証したという意味ではありません。

## ブラウザ確認の境界

この実行環境のChromiumには全URLナビゲーションをブロックする管理ポリシーがあり、ネイティブブラウザからループバックHTTPへの通し試験は実施できませんでした。管理ポリシーを変更・回避していません。

代わりに、実際のChromium DOMへローカルHTML/CSS/JavaScriptを読み込み、同じPythonエンジンへのメモリー内アダプターを用いてコンポーネント確認を実施しました。HTTPは別途実サーバへのPythonクライアントで検証しています。

したがって、11項目を「ネイティブブラウザHTTP E2E成功」と表現しません。HTML Blobの生成は検証しましたが、ネイティブダウンロード・OSファイル選択画面・ユーザー環境での起動は未検証です。`tools/browser_smoke.py` はその通し試験用として同梱しています。

## 自己レビューで追加した回帰確認

- 管理権限だけでは通信到達を成立させない。network_reachを1本以上通る必要があります。
- 評価後に入力モデルを変更しても過去レポートのシナリオ/資産スナップショットが変わらない。
- 比較で侵害起点変更、対象削除、対応対象変更、FAILED→UNKNOWNを解消件数に含めない。
- ブラウザで未反映JSONがある状態や点検中の入力変更によって、古い結果を表示しない。
- 極端に大きい整数はモデルエラーとして拒否し、整数→float変換のOverflowErrorで落ちない。
- JSON整数の桁数を独立して制限し、実行Pythonごとの整数変換制限に依存しない。
- 単独Unicodeサロゲートをレポート出力前に拒否する。

第三者・別エージェントによる独立したコードレビューやセキュリティ監査ではなく、実装者による自己レビューです。

## 未実施

実クラウド接続、クラウドテナント侵害、バックアップ/鍵破壊、復号/復元、実製品の構成確認、第三者レビュー、顧客受入、Windows/macOSでの動作、Python3.10での実行、GitHub Actionsの実行、GitHub/PyPI公開。

CIの定義はWindows/macOS/Linux × Python3.10/3.13を対象にしていますが、この環境で実行済みという意味ではありません。リリース後に実際のCI結果を確認してください。

## 再実行

```bash
python -m unittest discover -v
python -m cleanroomcheck demo --out verification-demo
```

任意の追加確認:

```bash
python -m coverage run --source=cleanroomcheck -m unittest discover
python -m coverage report -m
PYTHONPATH=. python tools/browser_component_smoke.py output/browser-components
```

最後のコマンドは開発用PlaywrightとChromiumが別途必要です。コア実行にこれらは不要です。CHROMIUM_PATH環境変数でブラウザ実行ファイルを指定できます。組織の端末・ブラウザ管理方針に従ってください。
