import { InboundEvent, OutboundReply } from "./common";

export type HttpClient = (url: string, init: RequestInit) => Promise<Response>;

export class LineAdapter {
  constructor(private readonly accessToken: string, private readonly http: HttpClient = fetch) {
    if (!accessToken) throw new Error("ACCESS_TOKEN is required");
  }

  parseEvent(payload: any): InboundEvent {
    const event = payload.events?.[0] ?? payload;
    const message = event.message ?? {};
    const kind = ({ text: "text", image: "image", audio: "audio", video: "video", file: "file" } as Record<string, string>)[message.type] ?? "text";
    const userId = event.source?.userId ?? payload.user_id;
    if (!userId) throw new Error("LINE event has no userId");
    return { platform: "line", user_id: String(userId), content_type: kind as InboundEvent["content_type"], text: message.text, media_url: message.id, reply_token: event.replyToken };
  }

  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> {
    if (!event.reply_token) throw new Error("LINE reply_token is required");
    const messages = reply.messages.slice(0, 5).map((message) => {
      if (message.type === "text") return { type: "text", text: message.text || message.media_url || "" };
      if (!message.media_url) throw new Error(`LINE ${message.type} reply requires media_url`);
      if (message.type === "image") return { type: "image", originalContentUrl: message.media_url, previewImageUrl: message.media_url };
      if (message.type === "audio") return { type: "audio", originalContentUrl: message.media_url, duration: 1000 };
      if (message.type === "video") return { type: "video", originalContentUrl: message.media_url, previewImageUrl: message.media_url };
      if (message.type === "file") return { type: "file", originalContentUrl: message.media_url, fileName: message.text || "attachment" };
      throw new Error(`Unsupported LINE content type: ${message.type}`);
    });
    const response = await this.http("https://api.line.me/v2/bot/message/reply", { method: "POST", headers: { Authorization: `Bearer ${this.accessToken}`, "Content-Type": "application/json" }, body: JSON.stringify({ replyToken: event.reply_token, messages }) });
    if (!response.ok) throw new Error(`LINE API error: ${response.status}`);
  }
}

export class TelegramAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) {
    if (!token) throw new Error("TELEGRAM_BOT_TOKEN is required");
  }

  parseEvent(payload: any): InboundEvent {
    const message = payload.message ?? payload.edited_message;
    if (!message?.from?.id || message.chat?.id === undefined) throw new Error("Telegram update has no supported message");
    const common = { platform: "telegram", user_id: String(message.from.id), reply_target: String(message.chat.id) };
    if (message.text !== undefined) return { ...common, content_type: "text", text: message.text };
    if (message.photo?.length) return { ...common, content_type: "image", media_url: `telegram:${message.photo.at(-1).file_id}` };
    for (const [type, key] of [["audio", "audio"], ["video", "video"], ["file", "document"]] as const) {
      if (message[key]) return { ...common, content_type: type, media_url: `telegram:${message[key].file_id}` };
    }
    throw new Error("Telegram content type is not supported");
  }

  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> {
    for (const message of reply.messages.slice(0, 10)) {
      const media = message.media_url?.replace(/^telegram:/, "");
      const methods: Record<string, [string, string]> = { image: ["sendPhoto", "photo"], audio: ["sendAudio", "audio"], video: ["sendVideo", "video"], file: ["sendDocument", "document"] };
      const [method, field] = methods[message.type] ?? ["sendMessage", "text"];
      if (message.type !== "text" && !media) throw new Error(`Telegram ${message.type} reply requires media_url`);
      const body: Record<string, string> = { chat_id: event.reply_target ?? event.user_id, [field]: message.type === "text" ? message.text : media! };
      if (message.type !== "text" && message.text) body.caption = message.text;
      const response = await this.http(`https://api.telegram.org/bot${this.token}/${method}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!response.ok) throw new Error(`Telegram API error: ${response.status}`);
    }
  }
}

export class DiscordAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) { if (!token) throw new Error("DISCORD_BOT_TOKEN is required"); }
  parseEvent(payload: any): InboundEvent {
    const message = payload.d ?? payload; const user = message.author?.id; const channel = message.channel_id;
    if (!user || !channel) throw new Error("Discord message has no channel or author");
    const common = { platform: "discord", user_id: String(user), reply_target: String(channel) };
    if (message.content) return { ...common, content_type: "text", text: message.content };
    const attachment = message.attachments?.[0]; if (!attachment?.url) throw new Error("Discord message has no supported content");
    return { ...common, content_type: DiscordAdapter.contentType(attachment.content_type, attachment.filename), media_url: attachment.url };
  }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> {
    if (!event.reply_target) throw new Error("Discord reply_target is required");
    const url = `https://discord.com/api/v10/channels/${event.reply_target}/messages`;
    for (const message of reply.messages.slice(0, 10)) {
      if (message.type === "text") await this.request(url, JSON.stringify({ content: (message.text ?? "").slice(0, 2000), allowed_mentions: { parse: [] } }), "application/json");
      else { if (!message.media_url) throw new Error(`Discord ${message.type} reply requires media_url`); const media = await this.http(message.media_url, {}); if (!media.ok) throw new Error("Discord media download failed"); const blob = await media.blob(); const form = new FormData(); form.append("payload_json", JSON.stringify({ content: (message.text || "").slice(0, 2000), allowed_mentions: { parse: [] } })); form.append("files[0]", blob, `attachment.${message.type}`); await this.request(url, form); }
    }
  }
  private async request(url: string, body: BodyInit, contentType?: string): Promise<void> { const headers: Record<string, string> = { Authorization: `Bot ${this.token}` }; if (contentType) headers["Content-Type"] = contentType; const response = await this.http(url, { method: "POST", headers, body }); if (!response.ok) throw new Error(`Discord API error: ${response.status}`); }
  static contentType(mime = "", filename = ""): InboundEvent["content_type"] { const value = `${mime} ${filename}`.toLowerCase(); if (value.startsWith("image/") || /\.(jpg|jpeg|png|gif|webp)$/.test(value)) return "image"; if (value.startsWith("audio/") || /\.(mp3|m4a|wav|ogg)$/.test(value)) return "audio"; if (value.startsWith("video/") || /\.(mp4|mov|webm)$/.test(value)) return "video"; return "file"; }
}

export class MastodonAdapter {
  constructor(private readonly baseUrl: string, private readonly token: string, private readonly http: HttpClient = fetch) { if (!baseUrl || !token) throw new Error("MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN are required"); }
  parseEvent(payload: any): InboundEvent { const status = payload.status ?? payload; const user = status.account?.id ?? status.user_id; if (!user) throw new Error("Mastodon status has no account"); const media = status.media_attachments?.[0]; const type = media ? MastodonAdapter.contentType(media.type) : "text"; return { platform: "mastodon", user_id: String(user), content_type: type, text: status.content ?? status.text, media_url: media?.url, reply_to_id: status.id ? String(status.id) : undefined }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> {
    for (const message of reply.messages.slice(0, 5)) {
      let mediaIds: string[] | undefined;
      if (message.type !== "text") {
        if (!message.media_url) throw new Error(`Mastodon ${message.type} reply requires media_url`);
        const media = await this.http(message.media_url, {});
        if (!media.ok) throw new Error("Mastodon media download failed");
        const form = new FormData();
        form.append("file", new Blob([await media.arrayBuffer()], { type: media.headers.get("content-type") ?? "application/octet-stream" }), `reply.${message.type}`);
        const upload = await this.http(`${this.baseUrl.replace(/\/$/, "")}/api/v2/media`, { method: "POST", headers: { Authorization: `Bearer ${this.token}` }, body: form });
        if (!upload.ok) throw new Error(`Mastodon media API error: ${upload.status}`);
        const uploaded = await upload.json() as { id?: string };
        if (!uploaded.id) throw new Error("Mastodon media upload returned no ID");
        mediaIds = [uploaded.id];
      }
      const body: Record<string, unknown> = { status: message.text ?? "", in_reply_to_id: event.reply_to_id ?? null };
      if (mediaIds) body.media_ids = mediaIds;
      const response = await this.http(`${this.baseUrl.replace(/\/$/, "")}/api/v1/statuses`, { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    }
  }
  static contentType(type: string): InboundEvent["content_type"] { return (["image", "audio", "video", "file"] as string[]).includes(type) ? type as InboundEvent["content_type"] : "file"; }
}

export class MisskeyAdapter {
  constructor(private readonly baseUrl: string, private readonly token: string, private readonly http: HttpClient = fetch) { if (!baseUrl || !token) throw new Error("MISSKEY_BASE_URL and MISSKEY_TOKEN are required"); }
  parseEvent(payload: any): InboundEvent { const note = payload.note ?? payload; const user = note.user?.id ?? note.userId; if (!user) throw new Error("Misskey note has no user"); const file = note.files?.[0]; const type = file ? MisskeyAdapter.contentType(file.type) : "text"; return { platform: "misskey", user_id: String(user), content_type: type, text: note.text, media_url: file?.id ?? file?.url, reply_to_id: note.id ? String(note.id) : undefined }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { const body: Record<string, unknown> = { i: this.token, text: message.text || message.media_url || "", replyId: event.reply_to_id ?? undefined }; if (message.type !== "text") { if (!message.media_url) throw new Error(`Misskey ${message.type} reply requires media_url`); body.fileIds = [message.media_url]; } const response = await this.http(`${this.baseUrl.replace(/\/$/, "")}/api/notes/create`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Misskey API error: ${response.status}`); } }
  static contentType(mime = ""): InboundEvent["content_type"] { if (mime.startsWith("image/")) return "image"; if (mime.startsWith("audio/")) return "audio"; if (mime.startsWith("video/")) return "video"; return "file"; }
}

export class BlueskyAdapter {
  constructor(private readonly serviceUrl: string, private readonly jwt: string, private readonly repo: string, private readonly http: HttpClient = fetch) { if (!serviceUrl || !jwt || !repo) throw new Error("BLUESKY_SERVICE_URL, BLUESKY_ACCESS_JWT and BLUESKY_REPO are required"); }
  parseEvent(payload: any): InboundEvent { const record = payload.record ?? payload; const author = payload.author ?? payload.did; if (!author || record.text === undefined) throw new Error("Bluesky post has no supported content"); return { platform: "bluesky", user_id: String(author), content_type: "text", text: record.text, reply_to_uri: payload.uri, reply_to_cid: payload.cid } as InboundEvent; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { const record: any = { $type: "app.bsky.feed.post", text: message.text, createdAt: new Date().toISOString() }; if (event.reply_to_uri && event.reply_to_cid) record.reply = { root: { uri: event.reply_to_uri, cid: event.reply_to_cid }, parent: { uri: event.reply_to_uri, cid: event.reply_to_cid } }; if (message.type !== "text") { if (!message.media_url) throw new Error(`Bluesky ${message.type} reply requires media_url`); if (message.type !== "image" && message.type !== "video") throw new Error(`Bluesky does not support ${message.type} post embeds`); const media = await this.http(message.media_url, {}); if (!media.ok) throw new Error("Bluesky media download failed"); const upload = await this.http(`${this.serviceUrl.replace(/\/$/, "")}/xrpc/com.atproto.repo.uploadBlob`, { method: "POST", headers: { Authorization: `Bearer ${this.jwt}`, "Content-Type": media.headers.get("content-type") ?? "application/octet-stream" }, body: await media.arrayBuffer() }); if (!upload.ok) throw new Error(`Bluesky Blob upload error: ${upload.status}`); const uploaded = await upload.json() as { blob?: unknown }; if (!uploaded.blob) throw new Error("Bluesky Blob upload returned no blob"); record.embed = message.type === "image" ? { $type: "app.bsky.embed.images", images: [{ alt: message.text ?? "", image: uploaded.blob }] } : { $type: "app.bsky.embed.video", video: uploaded.blob, alt: message.text ?? "" }; } const response = await this.http(`${this.serviceUrl.replace(/\/$/, "")}/xrpc/com.atproto.repo.createRecord`, { method: "POST", headers: { Authorization: `Bearer ${this.jwt}`, "Content-Type": "application/json" }, body: JSON.stringify({ repo: this.repo, collection: "app.bsky.feed.post", record }) }); if (!response.ok) throw new Error(`Bluesky API error: ${response.status}`); } }
}

export class SlackAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) { if (!token) throw new Error("SLACK_BOT_TOKEN is required"); }
  parseEvent(payload: any): InboundEvent { const event = payload.event ?? payload; const user = event.user ?? event.user_id; const channel = event.channel ?? event.channel_id; if (!user || !channel) throw new Error("Slack event has no user or channel"); const file = event.files?.[0]; const type = file ? SlackAdapter.contentType(file.mimetype, file.name) : "text"; return { platform: "slack", user_id: String(user), reply_target: String(channel), content_type: type, text: event.text, media_url: file?.url_private }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { const response = await this.http("https://slack.com/api/chat.postMessage", { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify({ channel: event.reply_target ?? event.user_id, text: message.text || message.media_url || "" }) }); if (!response.ok) throw new Error(`Slack HTTP error: ${response.status}`); const result = await response.json() as any; if (result.ok === false) throw new Error(`Slack API error: ${result.error ?? "unknown"}`); } }
  static contentType(mime = "", name = ""): InboundEvent["content_type"] { const value = `${mime} ${name}`.toLowerCase(); if (value.startsWith("image/") || /\.(png|jpe?g|gif|webp)$/.test(value)) return "image"; if (value.startsWith("audio/")) return "audio"; if (value.startsWith("video/")) return "video"; return "file"; }
}

export class MatrixAdapter {
  constructor(private readonly baseUrl: string, private readonly token: string, private readonly http: HttpClient = fetch) { if (!baseUrl || !token) throw new Error("MATRIX_BASE_URL and MATRIX_ACCESS_TOKEN are required"); }
  parseEvent(payload: any): InboundEvent { const event = payload.event ?? payload; const content = event.content ?? event; const room = event.room_id ?? payload.room_id; if (!room) throw new Error("Matrix event has no room_id"); const kind: Record<string, InboundEvent["content_type"]> = { "m.image": "image", "m.audio": "audio", "m.video": "video", "m.file": "file" }; return { platform: "matrix", user_id: String(event.sender ?? payload.user_id ?? ""), reply_target: String(room), content_type: kind[content.msgtype] ?? "text", text: content.body, media_url: content.url }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { if (!event.reply_target) throw new Error("Matrix room ID is required"); for (const [index, message] of reply.messages.slice(0, 5).entries()) { const content: any = message.type === "text" ? { msgtype: "m.text", body: message.text } : { msgtype: `m.${message.type}`, body: message.text || message.media_url, url: message.media_url }; const txn = `bot-${Date.now()}-${index}`; const response = await this.http(`${this.baseUrl.replace(/\/$/, "")}/_matrix/client/v3/rooms/${encodeURIComponent(event.reply_target)}/send/m.room.message/${txn}`, { method: "PUT", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify(content) }); if (!response.ok) throw new Error(`Matrix API error: ${response.status}`); } }
}

export class WhatsAppAdapter {
  constructor(private readonly token: string, private readonly phoneNumberId: string, private readonly http: HttpClient = fetch) { if (!token || !phoneNumberId) throw new Error("WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID are required"); }
  parseEvent(payload: any): InboundEvent { const value = payload.entry?.[0]?.changes?.[0]?.value ?? payload; const message = value.messages?.[0] ?? payload.message; if (!message?.from) throw new Error("WhatsApp webhook has no message"); const raw = message.type ?? "text"; const type = raw === "document" ? "file" : raw; const item = message[raw === "file" ? "document" : raw] ?? {}; return { platform: "whatsapp", user_id: String(message.from), content_type: type, text: item.body ?? item.caption, media_url: item.id }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { const url = `https://graph.facebook.com/v20.0/${this.phoneNumberId}/messages`; for (const message of reply.messages.slice(0, 5)) { const body: any = { messaging_product: "whatsapp", to: event.user_id, type: message.type === "file" ? "document" : message.type }; if (message.type === "text") body.text = { body: message.text }; else { if (!message.media_url) throw new Error(`WhatsApp ${message.type} reply requires media_url`); const key = body.type; body[key] = { id: message.media_url }; if (message.text && ["image", "video", "document"].includes(key)) body[key].caption = message.text; } const response = await this.http(url, { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`WhatsApp API error: ${response.status}`); } }
}

export class ViberAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) { if (!token) throw new Error("VIBER_AUTH_TOKEN is required"); }
  parseEvent(payload: any): InboundEvent { const sender = payload.sender ?? {}; const message = payload.message ?? {}; if (!sender.id) throw new Error("Viber event has no sender"); const type = message.type ?? "text"; return { platform: "viber", user_id: String(sender.id), content_type: type as InboundEvent["content_type"], text: message.text, media_url: message.media }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { if (message.type === "audio") throw new Error("Viber audio replies are not supported"); const body: any = { receiver: event.user_id, type: message.type }; if (message.type === "text") body.text = message.text; else { if (!message.media_url) throw new Error(`Viber ${message.type} reply requires media_url`); body.media = message.media_url; if (message.text) body.text = message.text; } const response = await this.http("https://chatapi.viber.com/pa/send_message", { method: "POST", headers: { "X-Viber-Auth-Token": this.token, "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Viber API error: ${response.status}`); } }
}

export class ZulipAdapter {
  constructor(private readonly baseUrl: string, private readonly email: string, private readonly apiKey: string, private readonly http: HttpClient = fetch) { if (!baseUrl || !email || !apiKey) throw new Error("ZULIP_BASE_URL, ZULIP_EMAIL and ZULIP_API_KEY are required"); }
  parseEvent(payload: any): InboundEvent { const message = payload.message ?? payload; const user = message.sender_email ?? message.sender_id; if (!user) throw new Error("Zulip message has no sender"); if (message.type === "stream") { if (!message.display_recipient || !message.subject) throw new Error("Zulip stream message has no stream or subject"); return { platform: "zulip", user_id: String(user), reply_target: String(message.display_recipient), reply_to_id: String(message.subject), reply_mode: "stream", content_type: "text", text: message.content ?? message.text }; } return { platform: "zulip", user_id: String(user), reply_mode: "direct", content_type: "text", text: message.content ?? message.text }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { const body: any = event.reply_mode === "stream" ? { type: "stream", to: event.reply_target, subject: event.reply_to_id, content: message.text || message.media_url || "" } : { type: "direct", to: event.user_id, content: message.text || message.media_url || "" }; const auth = btoa(`${this.email}:${this.apiKey}`); const response = await this.http(`${this.baseUrl.replace(/\/$/, "")}/api/v1/messages`, { method: "POST", headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(body) }); if (!response.ok) throw new Error(`Zulip API error: ${response.status}`); const result = await response.json() as any; if (result.result && result.result !== "success") throw new Error(`Zulip API error: ${result.msg ?? result.result}`); } }
}

export class GoogleChatAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) { if (!token) throw new Error("GOOGLE_CHAT_ACCESS_TOKEN is required"); }
  parseEvent(payload: any): InboundEvent { const message = payload.message ?? payload; const sender = message.sender ?? {}; const space = payload.space ?? {}; const user = sender.name ?? payload.user_id; const room = space.name ?? payload.space_name; if (!user || !room) throw new Error("Google Chat event has no sender or space"); const attachment = message.attachments?.[0] ?? message.attachment?.[0]; return { platform: "google_chat", user_id: String(user), reply_target: String(room), content_type: attachment ? "file" : "text", text: message.text, media_url: attachment?.downloadUri ?? attachment?.resourceName }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { if (!event.reply_target) throw new Error("Google Chat space is required"); for (const message of reply.messages.slice(0, 5)) { const response = await this.http(`https://chat.googleapis.com/v1/${event.reply_target}/messages`, { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify({ text: message.text || message.media_url || "" }) }); if (!response.ok) throw new Error(`Google Chat API error: ${response.status}`); } }
}

export class TeamsAdapter {
  constructor(private readonly token: string, private readonly serviceUrl: string, private readonly http: HttpClient = fetch) { if (!token || !serviceUrl) throw new Error("TEAMS_BOT_TOKEN and TEAMS_SERVICE_URL are required"); }
  parseEvent(payload: any): InboundEvent { const user = payload.from?.id ?? payload.user_id; const conversation = payload.conversation?.id; if (!user || !conversation) throw new Error("Teams activity has no sender or conversation"); const attachment = payload.attachments?.[0]; return { platform: "teams", user_id: String(user), reply_target: String(conversation), content_type: attachment ? "file" : "text", text: payload.text, media_url: attachment?.contentUrl }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { if (!event.reply_target) throw new Error("Teams conversation ID is required"); for (const message of reply.messages.slice(0, 5)) { const body: any = { type: "message", text: message.text || message.media_url || "" }; if (message.type !== "text" && message.media_url) body.attachments = [{ contentType: "application/octet-stream", contentUrl: message.media_url, name: "attachment" }]; const response = await this.http(`${this.serviceUrl.replace(/\/$/, "")}/v3/conversations/${encodeURIComponent(event.reply_target)}/activities`, { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Teams API error: ${response.status}`); } }
}

export class InstagramAdapter {
  constructor(private readonly token: string, private readonly accountId: string, private readonly http: HttpClient = fetch) { if (!token || !accountId) throw new Error("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID are required"); }
  parseEvent(payload: any): InboundEvent { const event = payload.entry?.[0]?.messaging?.[0] ?? payload; const message = event.message ?? payload.message ?? {}; const sender = event.sender ?? payload.sender ?? {}; if (!sender.id) throw new Error("Instagram event has no sender"); if (message.text !== undefined) return { platform: "instagram", user_id: String(sender.id), content_type: "text", text: message.text }; const attachment = message.attachments?.[0]; if (!attachment) throw new Error("Instagram event has no supported message"); const type = ["image", "audio", "video", "file"].includes(attachment.type) ? attachment.type : "file"; return { platform: "instagram", user_id: String(sender.id), content_type: type, media_url: attachment.payload?.url }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { const body: any = { recipient: { id: event.user_id } }; if (message.type === "text") body.message = { text: message.text }; else { if (!message.media_url) throw new Error(`Instagram ${message.type} reply requires media_url`); body.message = { attachment: { type: message.type, payload: { url: message.media_url } } }; } const response = await this.http(`https://graph.facebook.com/v20.0/${this.accountId}/messages`, { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Instagram API error: ${response.status}`); } }
}

export class RedditAdapter {
  constructor(private readonly token: string, private readonly http: HttpClient = fetch) { if (!token) throw new Error("REDDIT_ACCESS_TOKEN is required"); }
  parseEvent(payload: any): InboundEvent { const data = payload.data ?? payload; const user = data.author?.name ?? data.author ?? payload.user_id; const thing = data.name ?? data.id ?? payload.thing_id; if (!user || !thing) throw new Error("Reddit event has no author or thing ID"); return { platform: "reddit", user_id: String(user), content_type: "text", text: data.body ?? data.title ?? data.text, media_url: String(thing) }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { const thing = event.media_url; if (!thing) throw new Error("REDDIT_THING_ID is required for replies"); for (const message of reply.messages.slice(0, 5)) { const response = await this.http("https://oauth.reddit.com/api/comment", { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "User-Agent": "mini-sns-bot/1.0", "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ api_type: "json", thing_id: thing, text: message.text || message.media_url || "" }) }); if (!response.ok) throw new Error(`Reddit HTTP error: ${response.status}`); const result = await response.json() as any; if (result.json?.errors?.length) throw new Error(`Reddit API error: ${JSON.stringify(result.json.errors)}`); } }
}

export class TwitchAdapter {
  constructor(private readonly token: string, private readonly clientId: string, private readonly broadcasterId: string, private readonly senderId: string, private readonly http: HttpClient = fetch) { if (!token || !clientId || !broadcasterId || !senderId) throw new Error("Twitch credentials are required"); }
  parseEvent(payload: any): InboundEvent { const event = payload.event ?? payload; const user = event.chatter_user_id ?? event.user_id; const text = typeof event.message === "object" ? event.message.text : event.message ?? event.text; if (!user || text === undefined) throw new Error("Twitch event has no chat message"); return { platform: "twitch", user_id: String(user), content_type: "text", text: String(text), reply_to_id: event.message_id }; }
  async sendReply(event: InboundEvent, reply: OutboundReply): Promise<void> { for (const message of reply.messages.slice(0, 5)) { if (message.type !== "text") throw new Error("Twitch chat supports text replies only"); const body: any = { broadcaster_id: this.broadcasterId, sender_id: this.senderId, message: message.text }; if (event.reply_to_id) body.reply_parent_message_id = event.reply_to_id; const response = await this.http("https://api.twitch.tv/helix/chat/messages", { method: "POST", headers: { Authorization: `Bearer ${this.token}`, "Client-Id": this.clientId, "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error(`Twitch API error: ${response.status}`); const result = await response.json() as any; if (!result.data?.[0]?.is_sent) throw new Error("Twitch chat message was not sent"); } }
}

export class KakaoTalkAdapter {
  parseEvent(payload: any): InboundEvent { const request = payload.userRequest ?? {}; const user = request.user?.id ?? payload.user_id; if (!user) throw new Error("KakaoTalk request has no user"); return { platform: "kakaotalk", user_id: String(user), content_type: "text", text: request.utterance ?? "" }; }
  renderReply(reply: OutboundReply): any { return { version: "2.0", template: { outputs: reply.messages.slice(0, 3).map((message) => ({ simpleText: { text: message.text || message.media_url || "" } })) } }; }
}

export function createConfiguredAdapter(platform: string): any {
  const env = process.env;
  switch (platform) {
    case "line": return new LineAdapter(env.ACCESS_TOKEN ?? "");
    case "telegram": return new TelegramAdapter(env.TELEGRAM_BOT_TOKEN ?? "");
    case "discord": return new DiscordAdapter(env.DISCORD_BOT_TOKEN ?? "");
    case "mastodon": return new MastodonAdapter(env.MASTODON_BASE_URL ?? "", env.MASTODON_ACCESS_TOKEN ?? "");
    case "misskey": return new MisskeyAdapter(env.MISSKEY_BASE_URL ?? "", env.MISSKEY_TOKEN ?? "");
    case "bluesky": return new BlueskyAdapter(env.BLUESKY_SERVICE_URL ?? "https://bsky.social", env.BLUESKY_ACCESS_JWT ?? "", env.BLUESKY_REPO ?? "");
    case "slack": return new SlackAdapter(env.SLACK_BOT_TOKEN ?? "");
    case "matrix": return new MatrixAdapter(env.MATRIX_BASE_URL ?? "", env.MATRIX_ACCESS_TOKEN ?? "");
    case "whatsapp": return new WhatsAppAdapter(env.WHATSAPP_ACCESS_TOKEN ?? "", env.WHATSAPP_PHONE_NUMBER_ID ?? "");
    case "viber": return new ViberAdapter(env.VIBER_AUTH_TOKEN ?? "");
    case "zulip": return new ZulipAdapter(env.ZULIP_BASE_URL ?? "", env.ZULIP_EMAIL ?? "", env.ZULIP_API_KEY ?? "");
    case "google_chat": return new GoogleChatAdapter(env.GOOGLE_CHAT_ACCESS_TOKEN ?? "");
    case "teams": return new TeamsAdapter(env.TEAMS_BOT_TOKEN ?? "", env.TEAMS_SERVICE_URL ?? "");
    case "instagram": return new InstagramAdapter(env.INSTAGRAM_ACCESS_TOKEN ?? "", env.INSTAGRAM_ACCOUNT_ID ?? "");
    case "reddit": return new RedditAdapter(env.REDDIT_ACCESS_TOKEN ?? "");
    case "twitch": return new TwitchAdapter(env.TWITCH_ACCESS_TOKEN ?? "", env.TWITCH_CLIENT_ID ?? "", env.TWITCH_BROADCASTER_ID ?? "", env.TWITCH_SENDER_ID ?? "");
    case "kakaotalk": return new KakaoTalkAdapter();
    default: throw new Error(`Unsupported platform: ${platform}`);
  }
}
