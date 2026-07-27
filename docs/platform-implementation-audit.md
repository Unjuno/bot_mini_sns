# プラットフォーム調査・実装照合

調査資料（2026年7月26日）と、`python/platforms/` の実装を照合した結果です。

## 判定基準

- **部分実装**：受信イベントの一部と送信APIはあるが、調査資料の投稿種別・返信方式を満たさない。
- **共通契約のみ**：オフラインの共通イベント検証はできるが、実サービスの受信・返信実装としては未完成。
- **要実接続検証**：コード上のAPI経路はあるが、認証、署名、Webhook、メディア取得などの実サービス確認が必要。

「全17サービスのネイティブアダプターを実装済み」という表現は、実サービスで全種類を送受信できる意味では使わない。

| サービス | 調査資料との主な照合結果 | 現在の実装判定 |
| --- | --- | --- |
| LINE | 調査資料は `replyToken` を使う Reply API。イベントには返信トークンが必要 | **部分実装**。Reply APIへ修正済み。ただし画像・音声・動画・ファイルの送信は未実装 |
| Telegram | `message` の text/photo/audio/video/document の受信と各送信メソッドが必要 | **要実接続検証**。主要な受信・送信メソッドを実装 |
| Discord | Message Gateway、`MESSAGE_CONTENT` intent、チャンネルへのCreate Messageが必要 | **部分実装**。テキストとembed返信は実装。実ファイルmultipart送信・Gateway運用は未実装 |
| Zulip | メンション/DM受信、`/api/v1/messages` 返信、ファイルは別アップロード | **部分実装**。テキスト中心。添付の送受信は未実装 |
| Matrix | HomeserverごとのClient-Server API、room event、room IDが必要 | **部分実装**。受信・テキスト送信の形はあるが、イベント署名・メディア送信・正しいevent ID管理は未確認 |
| Slack | Events API、署名検証、`chat.postMessage`、private file URLの認証が必要 | **部分実装**。署名検証とメディア送信が未実装 |
| Google Chat | Chatアプリのイベント形式、同期応答またはChat APIの認証が必要 | **部分実装**。添付種別判定・イベント検証・返信形式が未完成 |
| Viber | Webhook、購読ユーザー、`send_message` の種別ごとのpayloadが必要 | **部分実装**。受信種別は読むが返信は常にtext |
| Mastodon | Status/Streaming API、返信には `in_reply_to_id`、メディアはupload後添付が必要 | **部分実装**。通常投稿であり、受信Statusへの返信・メディア送信が未実装 |
| Misskey | Notes/Streaming API、返信には `replyId`、ファイルはdrive uploadが必要 | **部分実装**。通常note投稿であり、返信・メディア送信が未実装 |
| Bluesky | AT Protocol record作成、返信には `reply` record、Blob uploadが必要 | **部分実装**。固定日時・通常投稿で、返信record・メディア送信が未実装 |
| WhatsApp | Cloud APIのWebhook、24時間会話制限、メディアID取得、種別ごとの送信が必要 | **部分実装**。受信IDをURLとして扱い、返信は常にtext |
| Instagram | Professionalアカウント向けMessaging API。WhatsApp APIとの共通化は不可 | **共通化不適合**。WhatsApp実装を継承しており、Instagram固有イベント・メディア処理が未完成 |
| Teams | Bot Framework Activity、serviceUrl、conversation reference、添付形式が必要 | **部分実装**。受信・返信の最小形のみで、Bot Frameworkの実運用要件を未検証 |
| KakaoTalk | 調査資料自身が通常投稿の受信・返信APIを未確定としている | **共通契約のみ**。callback URLへOpen Builder形式を返す実装で、汎用KakaoTalk Channel Botの実装とは断定不可 |
| Twitch | EventSub Chat Message受信、Helix Send Chat Message返信。画像等は対象外 | **部分実装**。テキスト経路はあるがEventSub署名・subscription管理が未実装 |
| Reddit | 投稿/コメントの文脈、OAuth、対象thingへのコメント返信が必要 | **部分実装**。テキストとthing IDの最小経路のみ。Devvit/API実環境は未検証 |

## 重要な結論

`PLATFORM_CATALOG` が全サービスについて `text/image/audio/video/file` の受信・送信を宣言していましたが、これは実装状況と一致しません。現在はオフライン共通契約の検証用宣言として扱い、実サービス対応済みという意味では扱わないものとします。

外部サービスの公式仕様との最終確認には、各サービスのBot登録、Webhook/Gateway設定、実トークン、テスト用イベントが必要です。ローカルテストだけで認証・署名・返信期限・メディアURLの有効性までは証明できません。
