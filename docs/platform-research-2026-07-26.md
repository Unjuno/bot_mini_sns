# プラットフォーム料金・利用条件調査

調査日：2026年7月26日（日本時間）  
目的：共存型マイクロSNSの**反応型（プル型）Botインテグレーション**先を選ぶため、各サービスの料金、無料枠、受信・返信方法を比較する。

## この調査でいうプル型

このシステムでは、Botからユーザーへ勝手に通知しない。
ユーザーが対応する投稿（文章・写真・音声・動画・ファイル）を送ったときだけ、次の処理を行う。

```text
ユーザーが入力
  ↓
サービスがBotへイベントを渡す
  ↓
Botが保存
  ↓
Botが同じやり取りへの返信として最近の投稿を返す
```

したがって、今回必要なのは一斉配信・予約通知・購読者へのPush送信ではない。比較では、次の機能を優先する。

- ユーザーから文章を受信できる
- ユーザーから写真を受信できる
- 受信イベントに対して返信できる
- Botからの能動的なPushなしで成立する
- 小規模利用で無料または低料金に収まる

## 結論

最初の候補は **Telegram** が最も扱いやすい。Bot PlatformとBot APIは無料で、ユーザー入力への受信・返信に向いている。
LINEは、日本のコミュニケーションプランでも返信メッセージが通数カウント対象外であるため、今回の「ユーザーの入力に対してReply APIで返すだけ」の方式なら、送信通数の面では実質的に無制限として扱える。ただし、Reply Tokenは1回のみ・Webhook受信後1分以内の使用が必要で、APIレート制限もある。[LINE公式リファレンス](https://developers.line.biz/ja/reference/messaging-api/nojs/)
Discordはグループ利用に向き、SlackとZulipはチーム・組織利用に向いている。

## 比較表

| プラットフォーム | Bot/API利用料 | 無料利用の条件・上限 | 今回のSNSとの相性 | 主な注意点 |
| --- | --- | --- | --- | --- |
| LINE | 返信メッセージは通数カウント対象外 | 日本のコミュニケーションプランは月額0円・月200通まで。ライトは月5,000円・5,000通、スタンダードは月15,000円・30,000通 | ◎ 日本の利用者に届きやすい | 公式アカウントが必要。Push配信を使わない今回の方式では無料枠を消費しないが、他の送信機能は別扱い |
| Telegram | 無料 | Bot PlatformとBot APIは無料。ユーザー入力への返信は無料で利用しやすい | ◎ 最初の追加候補 | ユーザーが先にBotへ入力する必要がある。大量配信の料金は今回の対象外 |
| Discord | APIの個別利用料は確認できず、無料サーバーで開始可能 | Botをサーバーへ追加し、受信イベントに返信。メッセージ受信には権限設定が必要 | ◎ グループ型コミュニティ向け | 個人SNSよりサーバー・チャンネル中心。能動的な通知は使わず、受信イベントへの返信だけを使う |
| Zulip | 無料枠あり | Cloud Freeは検索履歴10,000件・ファイル5GB。条件により無料Standardの対象。セルフホスト版はオープンソース | ○ 話題別コミュニティ向け | BotはメンションまたはDMなど受信条件がある。チーム利用向けの設計 |
| Matrix / Element | ホスティングによる | matrix.orgには無料枠があるが、添付10MB・データ100MB/日などの制限。自前Homeserverはサーバー費用が必要 | ○ 自由度・データ管理重視 | Homeserverの選択と運用が必要。無料枠・料金は変更される可能性がある |
| Slack | 無料プランあり | Freeはメッセージ履歴90日、最大10アプリ。Pro以上は有料。通常の非WorkflowアプリはFreeで開発可能 | △ チーム内利用向け | 全履歴利用や高度な機能は有料。一般向けSNSには向きにくい |
| Google Chat | API自体の一律料金は確認できず | Google CloudプロジェクトとChat API設定が必要。利用環境によってGoogle Workspace・Cloud側の条件を確認 | △ Google利用者向け | 認証・Cloud設定が他候補より複雑。一般公開型の入口には不向き |
| Viber | 商用条件 | 2024年2月5日以降、新規Botは商用条件での作成が必要。具体額は申請・契約時に確認 | ○ 個人向けメディア投稿 | 無料で始められる前提ではない |
| Mastodon | API利用料は基本なし | 既存インスタンスを利用する場合は各運営者の条件、自前運用ではサーバー・ストレージ費用 | ◎ SNS・タイムライン型 | インスタンス運用費と管理負担が必要 |
| Misskey | API利用料は基本なし | 既存インスタンスを利用する場合は各運営者の条件、自前運用ではサーバー・ストレージ費用 | ◎ SNS・タイムライン型 | インスタンスごとの仕様差を確認 |
| Bluesky | API利用料は基本なし | サービス利用料は無料で試せるが、レート制限・ホスティング・運用費は別 | ○ SNS型 | チャットBotではなく投稿・返信APIとして設計 |
| WhatsApp Business Cloud API | 会話・メッセージ課金の確認が必要 | Businessアカウント、Meta設定、無料枠・会話カテゴリ・テンプレート条件を確認 | ○ 機能面は有力 | 無料前提にしない。審査・料金体系が複雑 |

## 料金面での結論

試作コストを抑えるなら、Telegram、Discord、Mastodon、Misskey、Blueskyが候補になる。LINEは返信メッセージが料金カウント対象外のため、今回のプル型フローと相性が良い。Viberは新規Bot作成が商用条件になっているため、無料候補から外す。WhatsAppは料金・審査確認後に判断する。

なお、プラットフォーム料金が無料でも、Botを動かすRenderなどの実行環境、データベース、音声・動画・ファイル保存用ストレージの費用は別に発生する。

## 1回の返信で送れる量

| プラットフォーム | 1回の返信・送信で扱える量 | 今回の5件制限との関係 |
| --- | --- | --- |
| LINE | 1回のReply APIで最大5メッセージ | 直近5件のタイムラインなら十分 |
| Telegram | 通常はAPI呼び出し単位。写真・動画・音声・ファイルはMedia Groupで2〜10件をまとめられる | 5件制限でも十分。必要なら10件まで拡張可能 |
| Discord | 1メッセージに最大10 embeds、添付ファイルを含められる。リクエスト上限は25MiB | 5件の投稿を1返信へまとめる設計が可能 |
| Mastodon | 1つのStatusとして投稿し、メディアを添付する方式 | タイムライン5件は5投稿として返す設計が自然 |
| Viber | `send_message`で1メッセージを送信。複数件は個別送信 | 5件でも十分だが、送信回数はアダプターで管理 |
| Misskey / Bluesky | 投稿・返信APIを個別に呼び出す方式 | 5件を個別投稿として返す設計が自然 |

LINEの1回5メッセージ制限は、直近投稿を5件返す現在の仕様には十分である。各プラットフォームで送信単位が異なるため、共通仕様では「返信項目を最大5件」と定義し、アダプターが各サービスの送信形式へ変換する。[LINE公式リファレンス](https://developers.line.biz/ja/reference/messaging-api/nojs/)、[Telegram Bot API](https://core.telegram.org/bots/api)、[Discord Message API](https://docs.discord.com/developers/resources/message)

## 共通して必要なもの（プル型）

- Botアカウントまたはアプリの登録
- 各サービスのアクセストークン・署名鍵
- Webhookを受けるHTTPS公開URL、またはPolling/Gateway接続
- 共通SNS側のユーザーID変換処理
- 文章・写真・音声・動画・ファイルを共通投稿形式へ変換するアダプター
- データベースと画像保存先
- 利用規約、プライバシー、投稿削除方針

不要なもの：一斉Push配信、購読者リストへの定期通知、予約投稿、通知キュー、プラットフォーム横断のBroadcast機能。

## 投稿種別の対応調査

ここでは、ユーザー入力を受信し、タイムラインとして返信するために使えるかを比較する。
「対応」は共通形式へ変換しやすいこと、「要変換」はテキストや添付ファイルとして代替できるが、同じネイティブ表現ではないことを示す。

| 投稿種別 | LINE | Telegram | Discord | Zulip |
| --- | --- | --- | --- | --- |
| 文章 | 対応 | 対応 | 対応 | 対応 |
| 写真 | 対応 | 対応 | 対応 | 対応 |
| 音声 | 対応 | 対応 | 対応 | 対応 |
| 動画 | 対応 | 対応 | 対応 | 対応 |
| ファイル | 対応 | 対応 | 対応 | 対応 |

### LINE

LINEのMessaging APIには、テキスト、画像、動画、音声、ファイル、位置情報、スタンプのメッセージ種別がある。現在のLINE版のハンドラーと対応させやすい。

### Telegram

Telegram Bot APIは、受信`Message`にtext、photo、audio、video、document、location、stickerなどを含められる。送信側にも`sendMessage`、`sendPhoto`、`sendAudio`、`sendVideo`、`sendDocument`、`sendLocation`、`sendSticker`があるため、共通投稿種別との対応が最も素直である。

### Discord

DiscordのMessageはcontentとattachmentsを持ち、ファイル添付を扱える。メッセージ本文の取得には、サーバー設定と`MESSAGE_CONTENT` intentの確認が必要である。位置情報・スタンプは今回の共通仕様では対象外とする。

### Zulip

Zulipは文章メッセージとファイルアップロードを扱え、画像・動画・音声はプレビュー表示できる。今回の共通仕様では位置情報・スタンプを対象外とする。

### 追加調査プラットフォーム

| プラットフォーム | 文章 | 写真 | 音声 | 動画 | ファイル | 返信型の受信 | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Microsoft Teams | 対応 | 対応 | 要確認 | 要確認 | 対応（主にPersonal） | 対応 | 有力。企業・組織向け |
| Google Chat | 対応 | 添付対応 | 添付で要確認 | 添付で要確認 | 対応 | 対応 | 有力。Workspace向け |
| Matrix / Element | 対応 | メディア対応 | メディア対応 | メディア対応 | メディア対応 | SDK・Homeserver依存 | 有力。自由度重視 |
| Mattermost | 対応 | 添付・プラグイン依存 | 添付・プラグイン依存 | 添付・プラグイン依存 | 添付対応 | 受信方式を要確認 | セルフホスト向け |
| Slack | 対応 | 添付対応 | 添付対応 | 添付対応 | 添付対応 | 対応 | チーム向け |
| Viber | 対応 | 対応 | 要確認 | 対応 | 対応 | 対応 | 有力。個人向け |
| WhatsApp Business Cloud API | 対応 | メディア対応 | メディア対応 | メディア対応 | メディア対応 | 対応 | 料金・事業者審査に注意 |
| KakaoTalk Channel | 対応 | 要確認 | 要確認 | 要確認 | 要確認 | 条件付き | 韓国向け。API範囲を要確認 |
| Twitch Chat | 対応 | 対象外 | 対象外 | 対象外 | 対象外 | 対応 | 配信コミュニティ向け |
| Instagram Messaging | 対応 | 対応 | 要確認 | 要確認 | 要確認 | 対応 | Professionalアカウント前提 |
| Reddit / Devvit | 対応 | 対応 | 要確認 | 要確認 | 要確認 | 投稿・コメント返信 | SNS型だがチャットBotとは別設計 |
| Mastodon | 対応 | メディア対応 | メディア対応 | メディア対応 | メディア対応 | 対応 | 分散SNS向け |
| Bluesky | 対応 | 添付対応 | 要確認 | 要確認 | 要確認 | 投稿・返信API | AT Protocol向け |
| Misskey | 対応 | メディア対応 | メディア対応 | メディア対応 | メディア対応 | API・Streaming対応 | インスタンス依存 |

TeamsはBotがメッセージを受信して返信でき、個人チャットではファイルの送受信にも対応するが、チャンネル・グループではファイル条件が異なる。[Teams公式](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/build-conversational-capability)

Google ChatはChatアプリが同期的にイベントへ返信でき、メッセージ添付の取得APIもある。[Google Chat公式](https://developers.google.com/workspace/chat/receive-respond-interactions)

MatrixはHomeserverとSDKの選択が必要で、自由度は高いが運用負荷も高い。Mattermostはセルフホスト前提で、Webhookだけでは受信・返信の要件を満たさない場合があるため、別途Bot・プラグイン方式を確認する。

ViberはWebhookでユーザーからのメッセージを受信でき、Botからの返信も可能である。公式APIでは文章・画像・動画・ファイルを扱えるため、共通形式との対応は良い。ただし、ユーザーがBotを購読している必要があり、音声の扱いは追加確認が必要である。[Viber公式REST API](https://developers.viber.com/docs/api/rest-bot-api/)

WhatsApp Business Cloud APIはWebhookで受信でき、メディアメッセージも扱えるため機能面では有力である。一方、Businessアカウント、Webhook設定、Meta側の審査・料金体系が前提になるため、無料で気軽に試す候補ではない。[WhatsApp公式Webhook資料](https://www.postman.com/meta/whatsapp-business-platform/folder/vzaxn16/webhook-payload-reference)

KakaoTalk ChannelはWebhookを利用できるが、公式に確認できるWebhookはチャンネル追加・ブロック通知が中心である。今回の「ユーザー投稿を受信して返信する」用途では、KakaoTalk Channelのチャットボット機能と別APIの確認が必要なため、候補には残すが優先度は低くする。[Kakao Developers公式Webhook](https://developers.kakao.com/docs/en/kakaotalk-channel/callback)

TwitchはEventSubでチャットメッセージを受信し、APIでチャットへ返信できる。ただし、投稿の保存・タイムライン返信というより配信チャット向けで、画像やファイル投稿の共通インターフェースには向かない。[Twitch公式 Chat & Chatbots](https://dev.twitch.tv/docs/chat/)

Instagram MessagingはProfessionalアカウントを対象にメッセージWebhookを利用できるため候補になるが、通常のSNS投稿ではなくダイレクトメッセージ連携として扱うべきである。[Instagram公式Messaging Webhook](https://www.postman.com/meta/instagram/request/23987686-95cce6f6-b811-41dc-b560-d43741c5002a)

RedditはDevvitで投稿・コメントの読み書きができるが、一般的な1対1 Bot入力とは異なる。採用する場合は、Botアダプターではなく「投稿・コメントアダプター」として設計する。[Reddit公式API概要](https://developers.reddit.com/docs/capabilities/server/reddit-api)

MastodonはStreaming APIで公開投稿やダイレクトメッセージを受信でき、Status APIで投稿と返信ができる。分散SNSそのものに近いため、ADKomeのタイムライン思想とは相性が良い。[Mastodon公式Streaming API](https://docs.joinmastodon.org/methods/streaming/)

BlueskyはBot向けドキュメントと投稿・返信APIがあり、SNSアダプターとして有望である。ただし、チャットBotのような「受信した入力への即時返信」とはイベント設計が異なる。[Bluesky公式Bot・投稿ドキュメント](https://docs.bsky.app/docs/tutorials/creating-a-post)

MisskeyはNotes APIとStreaming APIを備え、投稿・メディア・返信を扱える。複数インスタンス間で仕様差があり得るため、Misskey.ioだけでなく対象インスタンスのAPI仕様を確認する必要がある。[Misskey公式Streaming API](https://misskey-hub.net/en/docs/for-developers/api/streaming/)

## 対応方針

共通インターフェースから投稿種別を削らない。各アダプターが次のような能力表を持つ。

```json
{
  "platform": "discord",
  "receive": ["text", "image", "audio", "video", "file"],
  "send": ["text", "image", "audio", "video", "file"]
}
```

## 実装優先順位

| 順位 | プラットフォーム | 理由 |
| --- | --- | --- |
| 1 | LINE | 現在の実装を基準に共通インターフェースを固める |
| 2 | Telegram | Bot APIが明確で、文章・写真・音声・動画・ファイルに対応しやすい |
| 3 | Mastodon | SNS・タイムライン型で、投稿・返信・メディアの考え方が本体仕様に近い |
| 4 | Viber | Webhookと返信に対応し、個人向けメディア投稿との相性が良い |
| 5 | Discord | コミュニティ運用に強いが、権限やサーバー設定の確認が必要 |
| 6 | Misskey / Bluesky | SNS型として有力だが、各API・イベントモデルへの適応が必要 |
| 7 | Zulip | 話題単位のコミュニティ向け。初期の単純なタイムラインにはやや過剰 |
| 8 | Teams / Google Chat / Slack | 企業・組織向け。利用目的が決まった後に追加 |
| 9 | WhatsApp / KakaoTalk / Instagram / Reddit / Twitch | 条件・用途が限定されるため、個別需要が出た時に追加 |

この順位では、まずLINEとTelegramでアダプターの共通構造を確認し、MastodonでSNS型アダプターを検証する。その後、Viber・Discordへ広げる。各アダプターは、実装前に受信イベント、返信期限、添付URLの有効期限、無料枠を確認する。

トークンや秘密鍵は設定ファイルへ保存せず、Renderなどの環境変数へ登録する。

## Renderの費用と注意点

RenderはBot本体を動かすインフラであり、各チャットサービスの料金とは別に考える。

- Free Web ServiceでPython/Flaskを公開できる
- 15分間アクセスがないと停止し、次のアクセス時に起動まで時間がかかる
- ローカルSQLite、アップロード画像などのファイルは再起動・再デプロイ・停止時に失われる可能性がある
- Free Postgresは1GBで、作成から30日後に期限切れになる制限がある
- 長期保存する場合は有料ストレージ、外部DB、または別の永続ストレージを検討する

したがって、試作・少人数の確認には無料構成、本番運用にはデータ保存費用を含む構成が必要になる。

## プル型での推奨調査・実装順

1. LINE：現在の実装を、ユーザー入力への返信だけに固定する。
2. Telegram：無料で試しやすく、個人向けBotとして追加する。
3. Discord：グループ・サーバー型の受信イベントへの返信として追加する。
4. Zulip：話題単位のコミュニティが必要になった場合に追加する。
5. Matrix、Slack、Google Chat：用途が決まった段階で個別に検証する。

## 公式情報

プラットフォームごとの料金・使い方・適合性は、[プラットフォーム別調査](platforms/README.md) に個別整理している。

- [LINE Messaging APIの料金](https://developers.line.biz/ja/docs/messaging-api/pricing/)
- [Telegram Bots](https://core.telegram.org/bots)
- [Telegram Bots FAQ（制限・有料ブロードキャスト）](https://core.telegram.org/bots/faq)
- [Discord Bots](https://docs.discord.com/developers/platform/bots)
- [Slack料金](https://api.slack.com/pricing)
- [Slack API・無料プランでの開発条件](https://api.slack.com/docs)
- [Zulip料金](https://zulip.com/plans/)
- [Zulip Interactive Bots API](https://docs.zulip.com/help/interactive-bots-api)
- [Matrix無料枠](https://www.matrix.org/try-matrix/)
- [Google Chat API](https://developers.google.com/workspace/chat/api/reference/rest)
- [Render無料プラン](https://render.com/docs/free)
- [LINE Messaging APIリファレンス](https://developers.line.biz/en/reference/messaging-api/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Discord Message Resource](https://docs.discord.com/developers/resources/message)
- [Zulipファイルアップロード](https://api.zulip.com/help/share-and-upload-files)
- [Viber REST Bot API](https://developers.viber.com/docs/api/rest-bot-api/)
- [WhatsApp Business Platform Webhook Payload](https://www.postman.com/meta/whatsapp-business-platform/folder/vzaxn16/webhook-payload-reference)
- [KakaoTalk Channel Webhook](https://developers.kakao.com/docs/en/kakaotalk-channel/callback)
- [Twitch Chat & Chatbots](https://dev.twitch.tv/docs/chat/)
- [Instagram Messaging Webhook](https://www.postman.com/meta/instagram/request/23987686-95cce6f6-b811-41dc-b560-d43741c5002a)
- [Reddit API概要](https://developers.reddit.com/docs/capabilities/server/reddit-api)
- [Mastodon Streaming API](https://docs.joinmastodon.org/methods/streaming/)
- [Bluesky投稿API](https://docs.bsky.app/docs/tutorials/creating-a-post)
- [Misskey Streaming API](https://misskey-hub.net/en/docs/for-developers/api/streaming/)

## 注意

料金・無料枠・API制限は変更される可能性がある。LINEについては、Push・Multicast・Broadcastなどを混ぜず、Reply APIだけを使うことが条件である。Push配信の料金比較は今回の要件には含めない。
