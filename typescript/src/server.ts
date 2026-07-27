import { createServer } from "node:http";
import { processEvent, InboundEvent } from "./common";

const posts: InboundEvent[] = [];
const server = createServer((request, response) => {
  if (request.method !== "POST") {
    response.writeHead(405, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: "POST required" }));
    return;
  }
  let body = "";
  request.setEncoding("utf8");
  request.on("data", (chunk: string) => { body += chunk; });
  request.on("end", () => {
    try {
      const reply = processEvent(JSON.parse(body) as InboundEvent, posts);
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify(reply));
    } catch (error) {
      response.writeHead(400, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: error instanceof Error ? error.message : "Invalid event" }));
    }
  });
});

server.listen(Number(process.env.PORT ?? 3000));
