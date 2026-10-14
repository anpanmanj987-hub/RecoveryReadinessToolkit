# 統合版の検証記録 — 2026-10-14

## 実行した検証

Windows、Node.js 24.19.0、Python 3.13.15で、修正版を統合した後に検証しました。
元アーカイブの検証記録は各プロジェクト内に保持し、今回の記録とは区別しています。

| 検証 | 統合後の結果 |
| --- | --- |
| リポジトリ外の作業場所から `python tools/verify.py` を絶対パスで実行 | 終了コード0 |
| BreakGlassMapのHTML再ビルド | 97,162バイト、外部資産なし |
| BreakGlassMapのNodeテスト | 86件成功、失敗・スキップ0 |
| CleanRoomCheckのPythonテスト（任意PyYAML導入済み） | 101件成功、失敗・スキップ0 |
| CleanRoomCheckのNode UI回帰テスト | 16件成功、失敗・スキップ0 |
| BreakGlassMapの実ブラウザー回帰（Edge、ローカルHTTP） | 依存条件の保持・証跡の維持と無効化が成功。ページ例外・外部リクエスト0 |
| CleanRoomCheckの実HTTPブラウザー操作（Edge） | 11項目成功。HTMLダウンロード、入力変更、結果フィルタ、390px表示を含む。ページ例外・外部リクエスト0 |
| BreakGlassMapのサンプルCLI入力検証 | 17ノード・4シナリオを検証、終了コード0 |
| CleanRoomCheckのCLIデモ生成 | 比較HTML・JSONと各レポートの生成成功、終了コード0 |

自動テストは計 **203件** です。ブラウザー操作の確認はこの件数と別に実施しました。
[統合テストの実行ログ](verification/local-tests.txt) と [統合後のブラウザー結果](verification/integrated-browser-results.json) を保存しています。

## 修正した主な問題

- BreakGlassMap：経路を変えないメタデータ保存で証跡が無効になる問題、明示的なnullが入力検証を通る問題、Windowsのブラウザー検証の文字コード問題。
- CleanRoomCheck：WindowsのCSV空行、不正Unicode・トークンによるHTTP例外、拒否POSTのTCP切断、レポート編集による共有出典データの破壊、非同期応答による新しい編集の上書き、入力途中の古い結果表示、初期取得前の操作、ブラウザー検証の文字コード問題。

再現手順、修正前の失敗、修正後の実行結果は、各 [BreakGlassMapレビュー](../BreakGlassMap/docs/REVIEW-2026-10-14.md) と [CleanRoomCheckレビュー](../CleanRoomCheck/docs/REVIEW-2026-10-14.md) を参照してください。

## 配布とレビュー

BreakGlassMapでは、実Chromeの全体スモークと直接HTML起動、配布用ZIP展開後の86テスト、53件の配布チェックサム一致も確認しました。
CleanRoomCheckでは、実EdgeのHTTPスモークとコンポーネントスモークを各11項目確認し、wheelを独立した仮想環境へインストールしてソース外からCLIデモを実行しました。

実装担当と別のレビュー担当が変更と統合構成を確認し、203件を独立して再実行しました。レビュー時に未解決の重大・中程度の指摘はありませんでした。

## GitHub Actions

[統合CIの定義](../.github/workflows/ci.yml) は以下を検証します。

- BreakGlassMap：Linux / Windows × Node.js 22 / 24。
- CleanRoomCheck：Linux / Windows / macOS × Python 3.10 / 3.13。PyYAMLとNode UI回帰も実行。
- ブラウザー：LinuxのPlaywright Chromiumで両ツールを検証。

この文書の表はローカルで観測した結果です。ホストされたCIの状態は [GitHub Actionsの実行一覧](https://github.com/anpanmanj987-hub/RecoveryReadinessToolkit/actions/workflows/ci.yml) で確認できます。
実際のクラウド環境や復旧訓練はこの検証に含まれません。
