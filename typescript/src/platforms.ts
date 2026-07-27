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
