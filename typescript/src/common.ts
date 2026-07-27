export type ContentType = "text" | "image" | "audio" | "video" | "file";

export const supportedPlatforms = [
  "line", "telegram", "discord", "zulip", "matrix", "slack", "google_chat",
  "viber", "mastodon", "misskey", "bluesky", "whatsapp", "instagram", "teams",
  "kakaotalk", "twitch", "reddit",
] as const;

export type InboundEvent = {
  platform: string;
  user_id: string;
  content_type: ContentType;
  text?: string;
  media_url?: string | null;
  reply_token?: string | null;
  reply_target?: string | null;
  reply_to_id?: string | null;
  reply_to_uri?: string | null;
  reply_to_cid?: string | null;
};

export type OutboundReply = {
  messages: Array<{ type: ContentType; text: string; media_url: string | null }>;
};

export function processEvent(event: InboundEvent, posts: InboundEvent[], limit = 5): OutboundReply {
  if (!(supportedPlatforms as readonly string[]).includes(event.platform)) {
    throw new Error(`Unsupported platform: ${event.platform}`);
  }
  posts.push(event);
  const selected = posts
    .filter((post) => post.content_type === event.content_type)
    .slice(-limit)
    .reverse();
  return {
    messages: selected.map((post) => ({
      type: post.content_type,
      text: post.text ?? "",
      media_url: post.media_url ?? null,
    })),
  };
}
