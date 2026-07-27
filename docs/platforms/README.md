# プラットフォーム別調査

調査日：2026年7月26日（日本時間）

各プラットフォームについて、料金、Botの利用方法、固定フローへの適合性を個別に整理する。

## 実装ステータス

全プラットフォームは `python/platforms/catalog.py` の共通契約に登録され、`create_adapter(name, offline=True)` で認証なしの検証ができます。
ネイティブAPIアダプターがあるものは公式API形式で送受信し、それ以外は `ConfiguredHTTPAdapter` で、各サービスのWebhook変換先を共通JSONへ接続できます。

### 検証方法

```powershell
cd python
python -m unittest discover -s tests -v
```

実サービスの認証情報なしでも、全17サービスについて受信イベントの検証、同一種類コンテンツの返信件数制限、送信ペイロードの生成をテストできます。
実サービスへ接続する場合は、ネイティブアダプターの環境変数、または未実装サービスの `<PLATFORM>_ADAPTER_ENDPOINT` と `<PLATFORM>_TOKEN` を設定します。

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
