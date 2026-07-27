# bot_mini_sns

チャットサービス上で動作する、対話型マイクロSNSの共通基盤です。
受信したコンテンツを保存し、同じプラットフォーム・同じ種類の最新コンテンツを、各プラットフォームの上限内で返信します。

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

Python版は各サービスの受信形式と送信APIをアダプターで吸収します。PHP・TypeScript・Go版は、同じ共通JSONイベントを受けるWebhookサーバーとして利用できます。

## Python版を起動する

PowerShellの場合：

```powershell
cd python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

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

`POST http://127.0.0.1:3000`へ共通イベントJSONを送信します。

### Go

```powershell
cd go
go run ./cmd/server
```

`POST http://127.0.0.1:8080/webhook`へ共通イベントJSONを送信します。

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

## ドキュメント

- [docs/core-spec.md](docs/core-spec.md)：MVP本体仕様
- [docs/architecture.md](docs/architecture.md)：共通基盤とアダプター境界
- [docs/openapi.yaml](docs/openapi.yaml)：共通HTTP/JSONインターフェース
- [docs/platforms/README.md](docs/platforms/README.md)：プラットフォーム別仕様
- [docs/implementation-languages.md](docs/implementation-languages.md)：言語別実装方針
- [docs/content-batch-spec.md](docs/content-batch-spec.md)：返信コンテンツの仕様

## ライセンス・公開範囲

現在は個人開発用のため、ライセンスは未設定です。公開後に利用条件を明確にする場合は、別途LICENSEを追加してください。
