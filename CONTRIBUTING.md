# 貢献方法

変更対象に応じて、[BreakGlassMap](BreakGlassMap/CONTRIBUTING.md) または [CleanRoomCheck](CleanRoomCheck/CONTRIBUTING.md) の貢献手順とモデル仕様を確認してください。

リポジトリのルートで `python tools/verify.py` を実行すると両プロジェクトを検証できます。YAMLのテストも実行する場合は、先に `python -m pip install "./CleanRoomCheck[yaml]"` を実行します。
ブラウザー関連の変更は、各プロジェクトのブラウザーテストでも確認してください。

プルリクエストでは再現手順、期待する動作、変更内容、実行した検証を記載してください。実際の資格情報・顧客データ・復旧手順の秘密情報をサンプルやテストに含めないでください。
