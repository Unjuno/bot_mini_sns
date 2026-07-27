export type ContentType = "text" | "image" | "audio" | "video" | "file";
export const MAX_EVENT_BODY_BYTES = 1024 * 1024;

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
  reply_mode?: string | null;
};

export type OutboundReply = {
  messages: Array<{ type: ContentType; text: string; media_url: string | null }>;
};

export class SQLitePostStore {
  private readonly database: any;

  constructor(path: string) {
    // node:sqlite is built into Node.js 22.5+; the server is intentionally dependency-light.
    const { DatabaseSync } = require("node:sqlite") as { DatabaseSync: new (path: string) => any };
    this.database = new DatabaseSync(path);
    this.database.exec(`CREATE TABLE IF NOT EXISTS platform_posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      platform TEXT NOT NULL, user_id TEXT NOT NULL, content_type TEXT NOT NULL,
      text TEXT, media_url TEXT, status TEXT NOT NULL DEFAULT 'published', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`);
    try { this.database.exec("ALTER TABLE platform_posts ADD COLUMN status TEXT NOT NULL DEFAULT 'published'"); } catch { /* existing schema already has it */ }
    this.database.exec(`CREATE TABLE IF NOT EXISTS processed_events (
      fingerprint TEXT PRIMARY KEY, response_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`);
  }

  claimEvent(fingerprint: string): OutboundReply | null {
    const row = this.database.prepare("SELECT response_json FROM processed_events WHERE fingerprint=?").get(fingerprint) as { response_json: string } | undefined;
    if (row) return JSON.parse(row.response_json) as OutboundReply;
    this.database.prepare("INSERT INTO processed_events (fingerprint, response_json) VALUES (?, ?)").run(fingerprint, JSON.stringify({ messages: [] }));
    return null;
  }

  completeEvent(fingerprint: string, response: OutboundReply): void {
    this.database.prepare("UPDATE processed_events SET response_json=? WHERE fingerprint=?").run(JSON.stringify(response), fingerprint);
  }

  releaseEvent(fingerprint: string): void {
    this.database.prepare("DELETE FROM processed_events WHERE fingerprint=?").run(fingerprint);
  }

  softDeletePost(id: number): boolean {
    const result = this.database.prepare("UPDATE platform_posts SET status='deleted' WHERE id=? AND status!='deleted'").run(id);
    return Number(result.changes) > 0;
  }

  close(): void { this.database.close(); }

  processEvent(event: InboundEvent, limit = 5): OutboundReply {
    if (!(supportedPlatforms as readonly string[]).includes(event.platform)) throw new Error(`Unsupported platform: ${event.platform}`);
    if (!event.user_id || !event.content_type) throw new Error("platform, user_id, and content_type are required");
    if (!( ["text", "image", "audio", "video", "file"] as string[]).includes(event.content_type)) throw new Error(`Unsupported content type: ${event.content_type}`);
    if (!Number.isInteger(limit) || limit < 1) throw new Error("limit must be a positive integer");
    if (event.platform.length > 32 || event.user_id.length > 256 || (event.text?.length ?? 0) > 10000 || (event.media_url?.length ?? 0) > 4096) throw new Error("event field exceeds maximum length");
    const insert = this.database.prepare("INSERT INTO platform_posts (platform,user_id,content_type,text,media_url) VALUES (?,?,?,?,?)");
    insert.run(event.platform, event.user_id, event.content_type, event.text ?? null, event.media_url ?? null);
    const rows = this.database.prepare("SELECT content_type AS type, COALESCE(text, '') AS text, media_url FROM platform_posts WHERE content_type=? AND status='published' ORDER BY id DESC LIMIT ?").all(event.content_type, limit) as Array<{ type: ContentType; text: string; media_url: string | null }>;
    return { messages: rows.map((row) => ({ type: row.type, text: row.text, media_url: row.media_url })) };
  }
}

export class PostgresPostStore {
  private readonly pool: any;
  readonly ready: Promise<void>;

  constructor(url: string) {
    const { Pool } = require("pg") as { Pool: new (options: { connectionString: string }) => any };
    this.pool = new Pool({ connectionString: url });
    this.ready = this.pool.query(`CREATE TABLE IF NOT EXISTS platform_posts (
      id BIGSERIAL PRIMARY KEY, platform TEXT NOT NULL, user_id TEXT NOT NULL,
      content_type TEXT NOT NULL, text TEXT, media_url TEXT,
      status TEXT NOT NULL DEFAULT 'published', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    ); CREATE TABLE IF NOT EXISTS processed_events (
      fingerprint TEXT PRIMARY KEY, response_json TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    ); CREATE INDEX IF NOT EXISTS platform_posts_content_type_id_idx ON platform_posts (content_type, id DESC);`).then(() => undefined);
  }

  async claimEvent(fingerprint: string): Promise<OutboundReply | null> {
    await this.ready;
    const existing = await this.pool.query("SELECT response_json FROM processed_events WHERE fingerprint=$1", [fingerprint]);
    if (existing.rows[0]) return JSON.parse(existing.rows[0].response_json) as OutboundReply;
    const inserted = await this.pool.query("INSERT INTO processed_events (fingerprint,response_json) VALUES ($1,$2) ON CONFLICT (fingerprint) DO NOTHING RETURNING fingerprint", [fingerprint, JSON.stringify({ messages: [] })]);
    if (inserted.rowCount === 0) {
      const concurrent = await this.pool.query("SELECT response_json FROM processed_events WHERE fingerprint=$1", [fingerprint]);
      return concurrent.rows[0] ? JSON.parse(concurrent.rows[0].response_json) as OutboundReply : null;
    }
    return null;
  }
  async completeEvent(fingerprint: string, response: OutboundReply): Promise<void> { await this.ready; await this.pool.query("UPDATE processed_events SET response_json=$1 WHERE fingerprint=$2", [JSON.stringify(response), fingerprint]); }
  async releaseEvent(fingerprint: string): Promise<void> { await this.ready; await this.pool.query("DELETE FROM processed_events WHERE fingerprint=$1", [fingerprint]); }
  async softDeletePost(id: number): Promise<boolean> { await this.ready; const result = await this.pool.query("UPDATE platform_posts SET status='deleted' WHERE id=$1 AND status!='deleted'", [id]); return result.rowCount > 0; }
  async processEvent(event: InboundEvent, limit = 5): Promise<OutboundReply> {
    if (!(supportedPlatforms as readonly string[]).includes(event.platform) || !event.user_id || !event.content_type) throw new Error("invalid event");
    if (!( ["text", "image", "audio", "video", "file"] as string[]).includes(event.content_type) || !Number.isInteger(limit) || limit < 1) throw new Error("invalid event");
    if (event.platform.length > 32 || event.user_id.length > 256 || (event.text?.length ?? 0) > 10000 || (event.media_url?.length ?? 0) > 4096) throw new Error("event field exceeds maximum length");
    await this.ready;
    const client = await this.pool.connect();
    try { await client.query("BEGIN"); await client.query("INSERT INTO platform_posts (platform,user_id,content_type,text,media_url) VALUES ($1,$2,$3,$4,$5)", [event.platform, event.user_id, event.content_type, event.text ?? null, event.media_url ?? null]); const rows = await client.query("SELECT content_type AS type, COALESCE(text, '') AS text, media_url FROM platform_posts WHERE content_type=$1 AND status='published' ORDER BY id DESC LIMIT $2", [event.content_type, limit]); await client.query("COMMIT"); return { messages: rows.rows.map((row: any) => ({ type: row.type, text: row.text, media_url: row.media_url })) }; } catch (error) { await client.query("ROLLBACK"); throw error; } finally { client.release(); }
  }
  async close(): Promise<void> { await this.pool.end(); }
}

export function processEvent(event: InboundEvent, posts: InboundEvent[], limit = 5): OutboundReply {
  if (!(supportedPlatforms as readonly string[]).includes(event.platform)) {
    throw new Error(`Unsupported platform: ${event.platform}`);
  }
  if (!event.user_id || !event.content_type) {
    throw new Error("platform, user_id, and content_type are required");
  }
  if (!(["text", "image", "audio", "video", "file"] as string[]).includes(event.content_type)) {
    throw new Error(`Unsupported content type: ${event.content_type}`);
  }
  if (!Number.isInteger(limit) || limit < 1) throw new Error("limit must be a positive integer");
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
