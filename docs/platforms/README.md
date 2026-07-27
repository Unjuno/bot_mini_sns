# プラットフォーム別調査

調査日：2026年7月26日（日本時間）

各プラットフォームについて、料金、Botの利用方法、固定フローへの適合性を個別に整理する。
調査内容と実装の照合結果は [プラットフォーム調査・実装照合](../platform-implementation-audit.md) を参照する。

## 実装ステータス

全17プラットフォームは `python/platforms/catalog.py` の共通契約に登録され、`create_adapter(name, offline=True)` で認証なしの検証ができます。Pythonには各プラットフォームの受信・返信経路の骨格がありますが、全サービスで全メディア種別の実サービス送受信が完了しているわけではありません。実装状況は照合表を確認してください。

### 検証方法

```powershell
cd python
python -m unittest discover -s tests -v
```

実サービスの認証情報なしでも、全17サービスについて共通イベントの検証、同一種類コンテンツの返信件数制限、送信ペイロードの生成をテストできます。これは外部APIへの接続成功を保証するものではありません。
実サービスへ接続する場合は、各ネイティブアダプターの環境変数を設定します。外部Webhookを使う場合は `ConfiguredHTTPAdapter` も利用できます。

## 必須設定一覧

| プラットフォーム | 必須環境変数 |
| --- | --- |
| LINE | `ACCESS_TOKEN`, `CHANNEL_SECRET` |
| Telegram | `TELEGRAM_BOT_TOKEN` |
| Discord | `DISCORD_BOT_TOKEN` |
| Zulip | `ZULIP_BASE_URL`, `ZULIP_EMAIL`, `ZULIP_API_KEY` |
| Matrix | `MATRIX_BASE_URL`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID` |
| Slack | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` |
| Google Chat | `GOOGLE_CHAT_ACCESS_TOKEN`, `GOOGLE_CHAT_SPACE`（必要時） |
| Viber | `VIBER_AUTH_TOKEN` |
| Mastodon | `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN` |
| Misskey | `MISSKEY_BASE_URL`, `MISSKEY_TOKEN` |
| Bluesky | `BLUESKY_ACCESS_JWT`, `BLUESKY_REPO` |
| WhatsApp | `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET` |
| Instagram | `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID` |
| Teams | `TEAMS_BOT_TOKEN`, `TEAMS_SERVICE_URL` |
| KakaoTalk | 現在の公式Channel webhookは追加・ブロック通知のみのため、投稿Bot用の実サービス設定は未提供 |
| Twitch | `TWITCH_ACCESS_TOKEN`, `TWITCH_CLIENT_ID`, `TWITCH_BROADCASTER_ID`, `TWITCH_SENDER_ID` |
| Reddit | `REDDIT_ACCESS_TOKEN`、返信対象に`REDDIT_THING_ID` |

未設定のプラットフォームは起動時に無理に初期化せず、`create_adapter(name, offline=True)`で認証なし検証を実行できます。

## 優先順位

1. [LINE](line.md)
2. [Telegram](telegram.md)
3. [Mastodon](mastodon.md)
4. [Viber](viber.md)
5. [Discord](discord.md)
6. [Misskey](misskey.md)
7. [Bluesky](bluesky.md)
8. [Zulip](zulip.md)

## 条件付き候補

- [Matrix / Element](matrix.md)
- [Microsoft Teams](teams.md)
- [Google Chat](google-chat.md)
- [Slack](slack.md)
- [WhatsApp Business Cloud API](whatsapp.md)
- [KakaoTalk](kakaotalk.md)
- [Twitch](twitch.md)
- [Instagram Messaging](instagram.md)
- [Reddit / Devvit](reddit.md)

総合比較は [platform-research-2026-07-26.md](../platform-research-2026-07-26.md) を参照する。
