import { strict as assert } from "node:assert";
import { test } from "node:test";
import { supportedPlatforms } from "./common";
import { LineAdapter, TelegramAdapter, DiscordAdapter, MastodonAdapter, MisskeyAdapter, BlueskyAdapter, SlackAdapter, MatrixAdapter, WhatsAppAdapter, ViberAdapter, ZulipAdapter, GoogleChatAdapter, TeamsAdapter, InstagramAdapter, RedditAdapter, TwitchAdapter } from "./platforms";

test("every implemented TypeScript adapter parses a representative webhook", () => {
  const cases: Array<[string, any, (payload: any) => any]> = [
    ["line", { events: [{ replyToken: "r", source: { userId: "u" }, message: { type: "text", text: "x" } }] }, new LineAdapter("token").parseEvent.bind(new LineAdapter("token"))],
    ["telegram", { message: { from: { id: 1 }, chat: { id: 2 }, text: "x" } }, new TelegramAdapter("token").parseEvent.bind(new TelegramAdapter("token"))],
    ["discord", { d: { channel_id: "c", author: { id: "u" }, content: "x" } }, new DiscordAdapter("token").parseEvent.bind(new DiscordAdapter("token"))],
    ["mastodon", { account: { id: "u" }, id: "s", content: "x" }, new MastodonAdapter("https://m.test", "token").parseEvent.bind(new MastodonAdapter("https://m.test", "token"))],
    ["misskey", { id: "n", userId: "u", text: "x" }, new MisskeyAdapter("https://m.test", "token").parseEvent.bind(new MisskeyAdapter("https://m.test", "token"))],
    ["bluesky", { author: "did:u", record: { text: "x" } }, new BlueskyAdapter("https://b.test", "jwt", "did:u").parseEvent.bind(new BlueskyAdapter("https://b.test", "jwt", "did:u"))],
    ["slack", { event: { user: "u", channel: "c", text: "x" } }, new SlackAdapter("token").parseEvent.bind(new SlackAdapter("token"))],
    ["matrix", { event: { sender: "@u:test", room_id: "!r:test", content: { msgtype: "m.text", body: "x" } } }, new MatrixAdapter("https://m.test", "token").parseEvent.bind(new MatrixAdapter("https://m.test", "token"))],
    ["whatsapp", { entry: [{ changes: [{ value: { messages: [{ from: "u", type: "text", text: { body: "x" } }] } }] }] }, new WhatsAppAdapter("token", "phone").parseEvent.bind(new WhatsAppAdapter("token", "phone"))],
    ["viber", { sender: { id: "u" }, message: { type: "text", text: "x" } }, new ViberAdapter("token").parseEvent.bind(new ViberAdapter("token"))],
    ["zulip", { message: { sender_email: "u@test", content: "x" } }, new ZulipAdapter("https://z.test", "u", "k").parseEvent.bind(new ZulipAdapter("https://z.test", "u", "k"))],
    ["google_chat", { space: { name: "spaces/1" }, message: { sender: { name: "users/1" }, text: "x" } }, new GoogleChatAdapter("token").parseEvent.bind(new GoogleChatAdapter("token"))],
    ["teams", { from: { id: "u" }, conversation: { id: "c" }, text: "x" }, new TeamsAdapter("token", "https://t.test").parseEvent.bind(new TeamsAdapter("token", "https://t.test"))],
    ["instagram", { entry: [{ messaging: [{ sender: { id: "u" }, message: { text: "x" } }] }] }, new InstagramAdapter("token", "account").parseEvent.bind(new InstagramAdapter("token", "account"))],
    ["reddit", { data: { author: { name: "u" }, body: "x", name: "t1_x" } }, new RedditAdapter("token").parseEvent.bind(new RedditAdapter("token"))],
    ["twitch", { event: { chatter_user_id: "u", message_id: "m", message: "x" } }, new TwitchAdapter("t", "c", "b", "s").parseEvent.bind(new TwitchAdapter("t", "c", "b", "s"))],
  ];
  for (const [platform, payload, parse] of cases) {
    const event = parse(payload);
    assert.equal(event.platform, platform);
    assert.equal(event.content_type, "text");
  }
  assert.ok(supportedPlatforms.includes("kakaotalk"));
});
