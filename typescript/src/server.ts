import { createServer } from "node:http";
import { createHash } from "node:crypto";
import { SQLitePostStore, PostgresPostStore, InboundEvent, MAX_EVENT_BODY_BYTES } from "./common";
import { createConfiguredAdapter } from "./platforms";
import { verifyHmacSha256, verifyHmacSha256Hex, verifySlackSignature } from "./security";

const storePath = process.env.TYPESCRIPT_DATABASE_PATH ?? "posts.sqlite";
const postStore = process.env.TYPESCRIPT_DATABASE_URL ? new PostgresPostStore(process.env.TYPESCRIPT_DATABASE_URL) : new SQLitePostStore(storePath);
const configuredPlatform = process.env.PLATFORM?.trim().toLowerCase();
const adapter = configuredPlatform ? createConfiguredAdapter(configuredPlatform) : null;
function replyLimitForPlatform(platform: string): number {
  if (platform === "telegram" || platform === "discord") return 10;
  if (platform === "kakaotalk") return 3;
  return 5;
}
const server = createServer(async (request, response) => {
  const adminMatch = request.url?.match(/^\/admin\/posts\/(\d+)$/);
  if (request.method === "DELETE" && adminMatch) {
    const expected = process.env.ADMIN_TOKEN ?? "";
    const auth = request.headers.authorization ?? "";
    if (!expected || auth !== `Bearer ${expected}`) { response.writeHead(403); response.end(JSON.stringify({ error: "forbidden" })); return; }
    const deleted = await postStore.softDeletePost(Number(adminMatch[1]));
    response.writeHead(deleted ? 200 : 404, { "content-type": "application/json" });
    response.end(JSON.stringify(deleted ? { id: Number(adminMatch[1]), status: "deleted" } : { error: "post not found" }));
    return;
  }
  if (request.method !== "POST") {
    response.writeHead(405, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: "POST required" }));
    return;
  }
  let body = "";
  request.setEncoding("utf8");
  request.on("data", (chunk: string) => { body += chunk; if (Buffer.byteLength(body, "utf8") > MAX_EVENT_BODY_BYTES) request.destroy(new Error("request body too large")); });
  request.on("end", async () => {
    let claimedFingerprint: string | null = null;
    try {
      if (configuredPlatform === "line") {
        const signature = request.headers["x-line-signature"];
        const secret = process.env.CHANNEL_SECRET ?? "";
        if (typeof signature !== "string" || !secret || !verifyHmacSha256(Buffer.from(body), secret, signature)) {
          response.writeHead(401, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "invalid LINE signature" }));
          return;
        }
      }
      if (configuredPlatform === "slack") {
        const timestamp = request.headers["x-slack-request-timestamp"];
        const signature = request.headers["x-slack-signature"];
        const secret = process.env.SLACK_SIGNING_SECRET ?? "";
        if (typeof timestamp !== "string" || typeof signature !== "string" || !secret || !verifySlackSignature(body, secret, timestamp, signature)) {
          response.writeHead(401, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "invalid Slack signature" }));
          return;
        }
      }
      if (configuredPlatform === "whatsapp") {
        const signature = request.headers["x-hub-signature-256"];
        const secret = process.env.WHATSAPP_APP_SECRET ?? "";
        if (typeof signature !== "string" || !secret || !verifyHmacSha256Hex(body, secret, signature, "sha256=")) {
          response.writeHead(401, { "content-type": "application/json" });
          response.end(JSON.stringify({ error: "invalid WhatsApp signature" }));
          return;
        }
      }
      const payload = JSON.parse(body);
      const event = adapter ? adapter.parseEvent(payload) : payload as InboundEvent;
      const fingerprint = createHash("sha256").update(`${event.platform}\0${body}`).digest("hex");
      const previous = await postStore.claimEvent(fingerprint);
      if (previous) {
        response.writeHead(200, { "content-type": "application/json" });
        response.end(JSON.stringify(previous));
        return;
      }
      claimedFingerprint = fingerprint;
      const reply = await postStore.processEvent(event, replyLimitForPlatform(event.platform));
      if (adapter) {
        if (typeof adapter.sendReply === "function") await adapter.sendReply(event, reply);
        else if (typeof adapter.renderReply === "function") {
          response.writeHead(200, { "content-type": "application/json" });
          await postStore.completeEvent(fingerprint, reply);
          response.end(JSON.stringify(adapter.renderReply(reply)));
          return;
        }
      }
      response.writeHead(200, { "content-type": "application/json" });
      await postStore.completeEvent(fingerprint, reply);
      response.end(JSON.stringify(reply));
    } catch (error) {
      if (claimedFingerprint) await postStore.releaseEvent(claimedFingerprint);
      console.error("Webhook processing failed", error);
      response.writeHead(400, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: "invalid webhook payload" }));
    }
  });
});

server.listen(Number(process.env.PORT ?? 3000));
process.on("exit", () => { void postStore.close(); });
