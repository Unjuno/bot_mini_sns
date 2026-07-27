# 開発ガイド

## 開発環境の準備

ルートで`.env.example`を`.env`へコピーします。実サービスの認証情報は`.env`にだけ設定し、Gitへコミットしません。

### Python

```powershell
cd python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### TypeScript

```powershell
cd typescript
npm ci
```

GoとPHPは、それぞれの公式実行環境をインストールしてください。

## 開発時の検証

変更後は次の順に実行します。

```powershell
# Python
cd python
python -m unittest discover -s tests
python check_setup.py --platform slack --offline

# TypeScript
cd ..\typescript
npm run build

# Go
cd ..\go
go test ./...

# PHP
cd ..\php
php -l src/common.php
php -l bin/server.php
```

外部サービスの認証情報を使わないオフライン検証では、`OFFLINE=true`を使用します。実サービスのWebhook確認は、対象サービスの認証情報・公開HTTPS URL・Webhook設定を用意した場合だけ行います。

## 実装の境界

- `python/app.py`：LINE署名付きWebhookとLINE固有の投稿・メディア処理
- `python/adapter_app.py`：Pythonのプラットフォームアダプター共通Webhook
- `python/core/`：保存・同種コンテンツ返信の共通ロジック
- `python/platforms/`：プラットフォーム固有の変換と送信
- `php/`、`typescript/`、`go/`：共通JSONイベントと17プラットフォームのWebhookを扱う各言語版Webhook
- `docs/core-spec.md`：現行仕様の正本

固定フローを変更する場合は、仕様・Pythonテスト・各言語版の共通契約を同時に更新します。翻訳、広告、検索、Push通知は現行仕様の対象外です。

## コミット前チェック

```powershell
git diff --check
git status --short
```

生成された各言語のSQLite、アップロードファイル、`.env`はコミットしません。公開前は[公開前チェックリスト](public-release-checklist.md)も確認します。
