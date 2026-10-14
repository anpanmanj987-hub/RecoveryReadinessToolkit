# GitHub公開前の確認

この配布物はまだGitHub/PyPIへ公開していません。公開先のアカウントや名前を勝手に決定していません。

## 内容と権利

MITライセンスを同梱しています。作者・組織の表記を確認してください。CleanRoomCheckという名称の商標、既存リポジトリ、PyPI名の空きは未確認です。必要に応じて名前を変更し、パッケージ名・コマンド・文書も統一してください。

架空例のみを含めてください。実在の会社名、テナントID、ネットワーク、ID/PW、内部パス、証跡資料、未公開の顧客事例を追加しないでください。実行結果も入力次第では機密情報になります。public demoのproject.demoはtrueを維持します。

## 手元で再確認

```bash
python -m unittest discover -v
python -m cleanroomcheck demo --out publish-check
```

YAML検証も実施するなら任意依存を導入してください。ブラウザ通し試験は組織のポリシーを満たすローカル端末で任意に実施します。CI定義があるだけでは実行済みと記載しないでください。

## 新しいリポジトリへ置く

ZIPはGit履歴を含みません。READMEのあるディレクトリで、公開先を自分で用意したうえで実行します。

```bash
git init
git add .
git commit -m "Initial CleanRoomCheck alpha"
git branch -M main
# 自分で作成した公開先URLに置き換える
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

GitHubの説明文例:

> Offline, evidence-aware design review for isolated recovery environments under cloud tenant compromise. Find shared administrative paths, key risks and restore assumptions — without cloud writes.

トピック例: cyber-recovery, cloud-security, backup, clean-room, resilience, security-tools。

## リリース記載

0.1.0a1はアルファです。クラウド収集・構築・復元・スキャナーは未実装、実クラウド・第三者検証未実施と明記してください。CIの成功後にのみ対応OS/バージョンの実行実績を追加します。名称変更を含む変更時はテスト、生成デモ、ドキュメントの整合を再確認します。

PyPIへの公開は別の明示的な作業です。名前の所有・認証・ビルド内容・依存関係を確認せずにアップロードしないでください。配布wheelはローカルインストール用として利用できます。
