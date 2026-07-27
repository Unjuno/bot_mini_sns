# bot_mini_sns — MVP完成版

チャットサービス上で動作する、対話型マイクロSNSの共通基盤です。
受信したコンテンツを保存し、同じプラットフォーム・同じ種類の最新コンテンツを、各プラットフォームの上限内で返信します。

現行MVPの実装と検証は完了しています。実サービスで利用する場合は、利用するサービスのBot登録、Webhook設定、認証情報の登録が別途必要です。

## MVPの仕様

```text
コンテンツを受信
  → プラットフォームと種類を判定
  → 保存
  → 同じプラットフォーム・同じ種類の最新コンテンツを返信
```

- 対応コンテンツ：文章、画像、音声、動画、ファイル
- コマンド、検索、翻訳、広告、Push通知は対象外
- 投稿者情報は内部処理で登録
- 実サービスの認証情報がなくても、全プラットフォームをオフライン検証可能

## 対応プラットフォーム

Pythonの`python/platforms/`に、次の17種類のアダプターを登録しています。

LINE、Telegram、Discord、Zulip、Matrix、Slack、Google Chat、Viber、Mastodon、Misskey、Bluesky、WhatsApp、Instagram、Microsoft Teams、KakaoTalk、Twitch、Reddit

Python版には各サービスの受信形式と送信APIを扱うアダプターがあります。実サービスで利用するには、各サービス側のBot登録・Webhook設定・認証情報が別途必要です。PHP・TypeScript・Go版は、各サービスのWebhookを共通JSONへ変換した後段として利用します。

## Python版を起動する

PowerShellの場合（ルートから実行）：

```powershell
cd python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

`python`ディレクトリから実行する場合は、`pip install -r requirements.txt`で同じ依存関係を導入できます。

起動確認：

```powershell
Invoke-WebRequest http://127.0.0.1:5000/
```

LINEで実際に使う場合は、ルートの`.env.example`を`.env`へコピーし、`ACCESS_TOKEN`と`CHANNEL_SECRET`を設定してください。`.env`はGitへ登録しません。

Renderなどでデプロイする場合は、Root Directoryを`python`に設定し、Build Commandを次にします。

```text
pip install -r requirements.txt
```

Start Commandの例：

```text
gunicorn app:app
```

## 認証なしで検証する

```powershell
cd python
python -m unittest discover -s tests -v
```

`create_adapter(name, offline=True)`を使うと、アカウントやアクセストークンなしで、17プラットフォームの共通イベント、返信件数制限、コンテンツ種別を検証できます。

起動前の設定確認：

```powershell
cd python
python check_setup.py --platform slack
python check_setup.py --platform slack --offline
```

不足している環境変数が表示されるため、設定後に通常起動してください。

共通Webhookサーバーを認証なしで試す場合：

```powershell
cd python
$env:PLATFORM = "slack"
$env:OFFLINE = "true"
python adapter_app.py
```

`POST http://127.0.0.1:5000/webhook`へ、プラットフォーム固有形式ではなく共通イベントJSONを送信します。実サービスで使う場合は`OFFLINE=false`にし、`docs/platforms/README.md`の必須設定を登録してください。投稿は`ADAPTER_DATABASE_PATH`のSQLiteへ保存されます。

他プラットフォームのネイティブWebhookをPythonで受ける場合は、RenderなどのRoot Directoryを`python`にし、Start Commandを次のようにします。`PLATFORM`と対象サービスの環境変数も登録してください。

```text
gunicorn adapter_app:app
```

LINEの署名検証とLINE固有の画像・音声・動画・ファイル処理は`gunicorn app:app`で起動する`app.py`が担当します。`adapter_app.py`は共通アダプター経路です。

## 他言語版

### PHP

```powershell
cd php
php -S 127.0.0.1:8081 -t bin
```

`POST http://127.0.0.1:8081/server.php`へ共通イベントJSONを送信します。

### TypeScript / Node.js

```powershell
cd typescript
npm install
npm run build
npm start
```

`POST http://127.0.0.1:3000`へ共通イベントJSONを送信します。TypeScriptサーバーはPOSTされたパスを問わず受信します。

### Go

```powershell
cd go
go run ./cmd/server
```

`POST http://127.0.0.1:8080/webhook`へ共通イベントJSONを送信します。

各言語版のWebhookは、外部サービスのWebhook形式を共通イベントJSONへ変換した後段で利用します。Pythonの`app.py`はLINEの署名付きWebhook本体、`python/platforms/`は各サービスのアダプターです。

共通イベントの例：

```json
{
  "platform": "slack",
  "user_id": "user-1",
  "content_type": "text",
  "text": "こんにちは"
}
```

## 検証コマンド

```powershell
# Python
cd python
python -m unittest discover -s tests

# TypeScript
cd ..\typescript
npm install
npx tsc --noEmit

# Go
cd ..\go
go test ./...

# PHP
cd ..\php
php -l src/common.php
php -l bin/server.php
```

GitHub Actionsでも同じ4言語の検証を実行します。外部サービスのアクセストークンはCIへ登録せず、ユニットテストと共通イベント検証のみを行います。

## ドキュメント

- [docs/core-spec.md](docs/core-spec.md)：MVP本体仕様
- [docs/architecture.md](docs/architecture.md)：共通基盤とアダプター境界
- [docs/openapi.yaml](docs/openapi.yaml)：共通HTTP/JSONインターフェース
- [docs/platforms/README.md](docs/platforms/README.md)：プラットフォーム別仕様
- [docs/implementation-languages.md](docs/implementation-languages.md)：言語別実装方針
- [docs/content-batch-spec.md](docs/content-batch-spec.md)：返信コンテンツの仕様
- [docs/configuration.md](docs/configuration.md)：環境変数・設定ファイル・デプロイ設定
- [docs/development.md](docs/development.md)：開発環境・検証・実装境界
- [docs/public-release-checklist.md](docs/public-release-checklist.md)：公開前の確認項目

## ライセンス・公開範囲

MIT Licenseです。詳細は[LICENSE](LICENSE)を確認してください。
