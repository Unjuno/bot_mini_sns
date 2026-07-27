import { createHmac, timingSafeEqual } from "node:crypto";

export function verifyHmacSha256(rawBody: string | Buffer, secret: string, provided: string, prefix = ""): boolean {
  const expected = createHmac("sha256", secret).update(rawBody).digest("base64");
  const actual = provided.startsWith(prefix) ? provided.slice(prefix.length) : provided;
  const left = Buffer.from(expected); const right = Buffer.from(actual);
  return left.length === right.length && timingSafeEqual(left, right);
}
