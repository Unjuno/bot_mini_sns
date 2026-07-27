# 設定ガイド

## まず設定するファイル

1. ルートの`.env.example`を`.env`へコピーする
2. LINEを使う場合は`ACCESS_TOKEN`と`CHANNEL_SECRET`を設定する
3. 画像・音声・動画・ファイルを返信する場合は、公開HTTPSでアクセスできる`MEDIA_BASE_URL`を設定する
4. `python/config.json`の投稿種別を必要に応じて変更する

秘密情報を含む`.env`、SQLiteデータベース、アップロードファイルはGitへ登録しません。
ホスティング環境などで既に環境変数が設定されている場合は、ホスティング側の値を優先します。

## Python LINEアプリ

`python/app.py`は、設定ファイルを次の優先順位で読み込みます。

| 設定 | 環境変数 | 未設定時 |
| --- | --- | --- |
| アプリ設定 | `CONFIG_PATH` | `python/config.json` |
| SQLite DB | `DATABASE_PATH` | `python/sns_bot.db` |
| メディア保存先 | `MEDIA_DIR` | `python/uploaded_media` |
| HTTPポート | `PORT` | `5000` |

相対パスは常に`python`ディレクトリを基準に解決されます。

## 共通プラットフォームWebhook

`python/adapter_app.py`を使う場合は、`.env`に次を設定します。相対パスは`python`ディレクトリを基準に解決されます。

```dotenv
PLATFORM=slack
OFFLINE=false
ADAPTER_DATABASE_PATH=adapter_posts.db
PORT=5000
```

`PLATFORM`は`docs/platforms/README.md`に記載された17プラットフォームのいずれかです。実サービス接続に必要な環境変数も同じ一覧に記載しています。

Renderなどでこの経路を公開する場合のStart Commandは`gunicorn adapter_app:app`です。LINE専用の`app.py`を使う場合は`gunicorn app:app`にします。`.env.example`はリポジトリルートに1つだけあり、`python`から起動しても同じファイルを読み込みます。

PHP版は`PHP_DATABASE_PATH`（既定値：`php/bin/posts.sqlite`）へSQLiteで投稿履歴を保存します。公開ホスティングでは、このパスに書き込み権限があることを確認してください。

外部データベースへ切り替える場合の共通契約、PostgreSQLのスキーマ、各言語での実装方針は[外部データベースへの切り替え](external-database.md)を参照してください。現行コードはSQLiteを標準実装としているため、`DATABASE_URL`を設定するだけでは外部DBへ切り替わりません。各言語版のRepository実装とマイグレーションが必要です。

起動前に`python check_setup.py --platform <platform>`を実行すると、必要な環境変数の不足を確認できます。アカウントなしの確認は`--offline`を付けます。

動作確認だけなら、認証情報なしで次を使えます。

```powershell
$env:PLATFORM="slack"
$env:OFFLINE="true"
python adapter_app.py
```

## Render

Python LINEアプリをRenderへデプロイする場合：

- Root Directory：`python`
- Build Command：`pip install -r requirements.txt`
- Start Command：`gunicorn app:app`
- Environment Variables：`.env`の値をRenderのEnvironmentへ登録

`MEDIA_DIR`のローカルファイルは永続ストレージがない環境では失われるため、画像等を継続保存する場合は永続ディスクまたは外部ストレージを用意します。
