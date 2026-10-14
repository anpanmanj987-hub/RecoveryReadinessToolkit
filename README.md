# RecoveryReadinessToolkit

クラウド障害・侵害時の復旧準備を、2つの観点からローカルで点検するOSSツール集です。
**BreakGlassMap** と **CleanRoomCheck** を1つのリポジトリに統合しています。

| ツール | 点検すること | 起動方法 |
| --- | --- | --- |
| [BreakGlassMap](BreakGlassMap/README.ja.md) | 認証・特権アクセス・資格情報・手順書の循環依存と、利用できる復旧経路 | `BreakGlassMap/dist/BreakGlassMap.html` をブラウザーで開く |
| [CleanRoomCheck](CleanRoomCheck/README.md) | テナント侵害時に使う隔離復旧環境の独立性と、判断を裏付ける証跡 | 下記のローカルサーバーを起動 |

## 使い始める

GitHubの「Code → Download ZIP」で取得・展開するか、次のコマンドで取得します。

```sh
git clone https://github.com/anpanmanj987-hub/RecoveryReadinessToolkit.git
cd RecoveryReadinessToolkit
```

BreakGlassMapの配布済みHTMLはインストール不要です。CLIを使う場合はNode.js 22以上が必要です。

```sh
cd BreakGlassMap
node bin/breakglassmap.mjs validate examples/identity-outage.json
node bin/breakglassmap.mjs analyze examples/identity-outage.json --scenario identity-outage --fail-on none --format json
```

CleanRoomCheckにはPython 3.10以上が必要です。リポジトリのルートから起動します。

```sh
cd CleanRoomCheck
python -m cleanroomcheck serve
```

表示されるローカルURLをブラウザーで開きます。サンプルの評価と比較レポートは次のコマンドで生成できます。

```sh
python -m cleanroomcheck demo --out demo-output
```

Windowsでは `CleanRoomCheck/launch_windows.cmd` も利用できます。
YAML入力を使う場合のみ、CleanRoomCheckフォルダー内で `python -m pip install ".[yaml]"` を実行します。

## 2つのツールを組み合わせる

1. BreakGlassMapで、IdP・PAM・資格情報・手順書が停止した場合の依存関係を可視化します。
2. 独立した復旧経路の候補を、CleanRoomCheckで隔離環境・バックアップ・ネットワーク・運用証跡の観点から点検します。
3. 各ツールのレポートと実際の復旧訓練の記録を、人が照合します。

両ツールのJSON形式と判定の意味は異なります。ファイルを相互に読み込ませる場合は、各ツールのモデルに沿って別々に記述してください。
共通の総合スコアや自動変換は提供していません。

サンプルは架空のデータです。判定は入力内容に基づく机上の評価であり、実環境での復旧成功を保証するものではありません。
詳しくは各ツールの [制限事項](BreakGlassMap/docs/LIMITATIONS.md)・[制限事項](CleanRoomCheck/docs/LIMITATIONS.md) を参照してください。

## 検証

Node.js 22以上とPython 3.10以上を用意し、リポジトリのルートから実行します。

```sh
python tools/verify.py
```

このコマンドはBreakGlassMapのHTML再ビルドとNodeテスト、CleanRoomCheckのPython・UIテストを順に実行し、失敗時に非ゼロで終了します。
PyYAML未導入時は任意のYAMLテストがスキップされます。
GitHub ActionsではWindows・Linuxと、CleanRoomCheckについてはmacOSでも検証します。

ブラウザーテストと修正内容の記録は [検証記録](docs/VERIFICATION.md) を参照してください。

## 構成とライセンス

```text
BreakGlassMap/     復旧経路の依存関係分析（JavaScript、オフラインHTML）
CleanRoomCheck/    隔離復旧環境の点検（Python、ローカルWeb UI）
tools/verify.py    両プロジェクトの検証入口
.github/workflows/ 統合リポジトリ用のCI
docs/             統合・検証・元アーカイブの記録
```

MIT License。両プロジェクトの原著作権表示とライセンスを保持しています。
[元アーカイブと統合方針](docs/PROVENANCE.md) / [貢献方法](CONTRIBUTING.md) / [セキュリティ](SECURITY.md)
