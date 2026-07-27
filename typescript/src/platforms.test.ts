import { strict as assert } from "node:assert";
import { test } from "node:test";
import { processEvent, supportedPlatforms } from "./common";
import { LineAdapter, TelegramAdapter, DiscordAdapter, MastodonAdapter, MisskeyAdapter, BlueskyAdapter, SlackAdapter, MatrixAdapter, WhatsAppAdapter, ViberAdapter, ZulipAdapter, GoogleChatAdapter, TeamsAdapter, InstagramAdapter, RedditAdapter, TwitchAdapter, KakaoTalkAdapter } from "./platforms";

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
    ["kakaotalk", { userRequest: { user: { id: "u" }, utterance: "x" } }, new KakaoTalkAdapter().parseEvent.bind(new KakaoTalkAdapter())],
  ];
  for (const [platform, payload, parse] of cases) {
    const event = parse(payload);
    assert.equal(event.platform, platform);
    assert.equal(event.content_type, "text");
  }
  assert.ok(supportedPlatforms.includes("kakaotalk"));
});

test("every TypeScript adapter sends a text reply through the HTTP seam", async () => {
  const calls: string[] = [];
  const http = async (url: string, init: RequestInit): Promise<Response> => {
    calls.push(`${init.method ?? "GET"} ${url}`);
    return new Response(JSON.stringify({ ok: true, result: "success", data: [{ is_sent: true }] }), { status: 200, headers: { "content-type": "application/json" } });
  };
  const reply = { messages: [{ type: "text" as const, text: "reply", media_url: null }] };
  await new LineAdapter("token", http).sendReply({ platform: "line", user_id: "u", content_type: "text", reply_token: "r" }, reply);
  await new TelegramAdapter("token", http).sendReply({ platform: "telegram", user_id: "u", content_type: "text", reply_target: "c" }, reply);
  await new DiscordAdapter("token", http).sendReply({ platform: "discord", user_id: "u", content_type: "text", reply_target: "c" }, reply);
  await new MastodonAdapter("https://m.test", "token", http).sendReply({ platform: "mastodon", user_id: "u", content_type: "text", reply_to_id: "s" }, reply);
  await new MisskeyAdapter("https://m.test", "token", http).sendReply({ platform: "misskey", user_id: "u", content_type: "text", reply_to_id: "n" }, reply);
  await new BlueskyAdapter("https://b.test", "jwt", "did:u", http).sendReply({ platform: "bluesky", user_id: "u", content_type: "text" }, reply);
  await new SlackAdapter("token", http).sendReply({ platform: "slack", user_id: "u", content_type: "text", reply_target: "c" }, reply);
  await new MatrixAdapter("https://m.test", "token", http).sendReply({ platform: "matrix", user_id: "u", content_type: "text", reply_target: "!r:test" }, reply);
  await new WhatsAppAdapter("token", "phone", http).sendReply({ platform: "whatsapp", user_id: "u", content_type: "text" }, reply);
  await new ViberAdapter("token", http).sendReply({ platform: "viber", user_id: "u", content_type: "text" }, reply);
  await new ZulipAdapter("https://z.test", "u", "k", http).sendReply({ platform: "zulip", user_id: "u", content_type: "text", reply_mode: "direct" }, reply);
  await new GoogleChatAdapter("token", http).sendReply({ platform: "google_chat", user_id: "u", content_type: "text", reply_target: "spaces/1" }, reply);
  await new TeamsAdapter("token", "https://t.test", http).sendReply({ platform: "teams", user_id: "u", content_type: "text", reply_target: "c" }, reply);
  await new InstagramAdapter("token", "account", http).sendReply({ platform: "instagram", user_id: "u", content_type: "text" }, reply);
  await new RedditAdapter("token", http).sendReply({ platform: "reddit", user_id: "u", content_type: "text", media_url: "t1_x" }, reply);
  await new TwitchAdapter("t", "c", "b", "s", http).sendReply({ platform: "twitch", user_id: "u", content_type: "text" }, reply);
  const kakao = new KakaoTalkAdapter().renderReply(reply);
  assert.equal(kakao.version, "2.0");
  assert.equal(calls.length, 16);
});

test("TypeScript common core validates events and shares same-type posts across platforms", () => {
  const posts: any[] = [];
  processEvent({ platform: "line", user_id: "u", content_type: "text", text: "line" }, posts);
  const reply = processEvent({ platform: "telegram", user_id: "u2", content_type: "text", text: "telegram" }, posts);
  assert.deepEqual(reply.messages.map((message) => message.text), ["telegram", "line"]);
  assert.throws(() => processEvent({ platform: "line", user_id: "", content_type: "text" }, posts), /required/);
  assert.throws(() => processEvent({ platform: "line", user_id: "u", content_type: "unknown" as any }, posts), /Unsupported content type/);
});
