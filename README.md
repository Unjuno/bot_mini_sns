# ADKome

大手チャットサービスと共存する、対話型マイクロSNSの基盤です。
LINEなどのBotを入口にして、文章・写真・音声・動画・ファイルを保存し、最新のタイムラインを返信します。対応種別はプラットフォームごとに異なります。

## 固定フロー

```text
最初の投稿 → 保存 → 使い方を返信
次の投稿   → 保存 → 最近の投稿を返信
```

ユーザー登録操作、キーワード、コマンド、検索、Push通知はありません。ユーザー情報の登録は内部処理として行います。

## 構成

```text
LINE / Telegram / Discordなど
          ↓
   プラットフォームアダプター
          ↓
      共通SNS処理
          ↓
   投稿保存・タイムライン返信
```

将来追加する機能は、返信直前のブラックボックス拡張である翻訳と広告だけです。

## 開発

```powershell
cd python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

環境変数は`.env.example`（ルート）を参考に設定してください。秘密情報はGitへ登録しません。

## テスト

```powershell
# Python
cd python
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Lean形式検証（ルートから）
lean formal\FixedFlow.lean
```

## 資料

本体仕様の正本は[docs/core-spec.md](docs/core-spec.md)です。

- [docs/README.md](docs/README.md)：資料一覧
- [docs/core-spec.md](docs/core-spec.md)：確定MVP仕様
- [docs/user-flow.md](docs/user-flow.md)：固定ユーザーフロー
- [docs/architecture.md](docs/architecture.md)：共通基盤と拡張境界
- [docs/openapi.yaml](docs/openapi.yaml)：共通HTTP/JSONインターフェース
- [docs/future-vision.md](docs/future-vision.md)：翻訳・広告の将来構想
- [formal/FixedFlow.lean](formal/FixedFlow.lean)：Lean 4形式証明
