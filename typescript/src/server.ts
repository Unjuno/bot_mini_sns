import { createServer } from "node:http";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { processEvent, InboundEvent } from "./common";
import { createConfiguredAdapter } from "./platforms";
import { verifyHmacSha256 } from "./security";

const storePath = process.env.POSTS_FILE ?? "posts.json";
const posts: InboundEvent[] = existsSync(storePath)
  ? JSON.parse(readFileSync(storePath, "utf8")) as InboundEvent[]
  : [];
const configuredPlatform = process.env.PLATFORM?.trim().toLowerCase();
const adapter = configuredPlatform ? createConfiguredAdapter(configuredPlatform) : null;
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
      const payload = JSON.parse(body);
      const event = adapter ? adapter.parseEvent(payload) : payload as InboundEvent;
      const reply = processEvent(event, posts);
      writeFileSync(storePath, JSON.stringify(posts, null, 2));
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
