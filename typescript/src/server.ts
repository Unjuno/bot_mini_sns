import { createServer } from "node:http";
import { SQLitePostStore, InboundEvent } from "./common";
import { createConfiguredAdapter } from "./platforms";
import { verifyHmacSha256, verifyHmacSha256Hex, verifySlackSignature } from "./security";

const storePath = process.env.TYPESCRIPT_DATABASE_PATH ?? "posts.sqlite";
const postStore = new SQLitePostStore(storePath);
const configuredPlatform = process.env.PLATFORM?.trim().toLowerCase();
const adapter = configuredPlatform ? createConfiguredAdapter(configuredPlatform) : null;
const replyLimit = configuredPlatform === "telegram" || configuredPlatform === "discord" ? 10 : configuredPlatform === "kakaotalk" ? 3 : 5;
const server = createServer((request, response) => {
  if (request.method !== "POST") {
    response.writeHead(405, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: "POST required" }));
    return;
  }
  let body = "";
  request.setEncoding("utf8");
  request.on("data", (chunk: string) => { body += chunk; });
  request.on("end", async () => {
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
      const reply = postStore.processEvent(event, replyLimit);
      if (adapter) {
        if (typeof adapter.sendReply === "function") await adapter.sendReply(event, reply);
        else if (typeof adapter.renderReply === "function") {
          response.writeHead(200, { "content-type": "application/json" });
          response.end(JSON.stringify(adapter.renderReply(reply)));
          return;
        }
      }
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify(reply));
    } catch (error) {
      response.writeHead(400, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: error instanceof Error ? error.message : "Invalid event" }));
    }
  });
});

server.listen(Number(process.env.PORT ?? 3000));
process.on("exit", () => postStore.close());
