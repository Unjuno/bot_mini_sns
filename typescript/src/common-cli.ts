import * as readline from "node:readline";
import { InboundEvent, processEvent } from "./common";

const posts: InboundEvent[] = [];
const input = readline.createInterface({ input: process.stdin });
input.on("line", (line) => {
  const event = JSON.parse(line) as InboundEvent;
  process.stdout.write(`${JSON.stringify(processEvent(event, posts))}\n`);
});
