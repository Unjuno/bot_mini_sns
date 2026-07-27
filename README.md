# bot_mini_sns

大手チャットサービスと共存する、対話型マイクロSNSの基盤です。
Python版・LINEを基準実装として、文章・写真・音声・動画・ファイルを保存し、同種コンテンツを返信します。その他のプラットフォームと言語は共通契約に沿って順次追加します。

## 固定フロー

```text
コンテンツを送信 → 保存 → 同じプラットフォーム・同じ種類の最新コンテンツを最大数返信
```

ユーザー登録操作、キーワード、コマンド、検索、Push通知はありません。ユーザー情報の登録は内部処理として行います。

## 構成

```text
LINE（現行実装）
          ↓
   LINEアダプター
          ↓
      共通SNS処理
          ↓
   投稿保存・タイムライン返信
```

翻訳と広告は現在のMVPおよび直近の実装対象に含めません。

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
- [docs/future-vision.md](docs/future-vision.md)：保留中の将来アイデア
- [formal/FixedFlow.lean](formal/FixedFlow.lean)：Lean 4形式証明
