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
