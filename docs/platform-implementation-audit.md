# プラットフォーム実装監査

この表は、`python/platforms/` の現在のコードと、実サービスの運用に必要な条件を分けて示します。
「オフライン契約」は、共通イベントをローカルで検証できるという意味であり、トークンを設定すれば本番動作するという意味ではありません。

## 本番対応の判定

| サービス | コード上の受信・返信アダプター | 本番起動 | 残っている確認・制約 |
| --- | --- | --- | --- |
| LINE | あり。Reply Tokenを使う | **許可** | 実トークン、Webhook署名、各メディア種別の実送受信を確認する |
| Telegram | あり | **オフラインのみ** | Webhook設定、Bot APIの実イベント、メディア取得を確認する |
| Discord | あり | **オフラインのみ** | Gateway接続、Intent、multipart添付送信を確認する |
| Zulip | あり | **オフラインのみ** | Webhook/API認証、DM・stream返信、添付を確認する |
| Matrix | あり | **オフラインのみ** | sync購読、イベント除外、メディアアップロードを確認する |
| Slack | あり | **オフラインのみ** | Events API署名、URL検証、private file取得を確認する |
| Google Chat | あり | **オフラインのみ** | Chatアプリの認証、イベント形式、添付取得を確認する |
| Viber | あり | **オフラインのみ** | Webhook登録、購読状態、各メディアpayloadを確認する |
| Mastodon | あり | **オフラインのみ** | Streaming/Webhook入口、メディアアップロードを確認する |
| Misskey | あり | **オフラインのみ** | Streaming入口、Drive upload、実返信を確認する |
| Bluesky | あり | **オフラインのみ** | AT Protocol認証、reply record、Blob uploadを確認する |
| WhatsApp | あり | **オフラインのみ** | Webhook署名、メディアID取得、24時間制限を確認する |
| Instagram | あり。WhatsAppとは別実装 | **オフラインのみ** | Professional accountのWebhook、権限、メディア形式を確認する |
| Teams | あり | **オフラインのみ** | Bot Framework署名、serviceUrl、conversation referenceを確認する |
| KakaoTalk | Kakao Open Builderの受信・返信レンダリング | **オフラインのみ** | 一般的なChannel webhookを汎用SNS受信と見なさない。Open Builderの実環境で形式・運用条件を確認する |
| Twitch | あり。テキストチャットのみ | **オフラインのみ** | EventSub署名・subscription管理・Helix返信を確認する |
| Reddit | あり。コメント返信の最小経路 | **オフラインのみ** | OAuth、thing ID、APIエラー、実サブレディットで確認する |

## 実装上の不変条件

- 本番起動の許可状態は `python/platforms/catalog.py` の `PRODUCTION_READY` を正とする。
- `python/check_setup.py` と `python/adapter_app.py` は同じ許可状態を参照する。
- `create_adapter(name, offline=True)` は全17サービスの共通契約を認証なしで検証できる。
- `offline=False` では、未検証サービスを「キーがあるから」という理由だけで起動しない。
- ヘルスチェックは未起動時に `503` と `status: not_ready` を返す。

実サービスの認証、署名、Webhook、返信期限、メディアURLの有効性は、各サービスのテスト用アカウントによる接続検証なしには証明できません。
