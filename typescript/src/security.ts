import { createHmac, timingSafeEqual } from "node:crypto";

export function verifyHmacSha256(rawBody: string | Buffer, secret: string, provided: string, prefix = ""): boolean {
  const expected = createHmac("sha256", secret).update(rawBody).digest("base64");
  const actual = provided.startsWith(prefix) ? provided.slice(prefix.length) : provided;
  const left = Buffer.from(expected); const right = Buffer.from(actual);
  return left.length === right.length && timingSafeEqual(left, right);
}

export function verifyHmacSha256Hex(rawBody: string | Buffer, secret: string, provided: string, prefix = ""): boolean {
  const expected = createHmac("sha256", secret).update(rawBody).digest("hex");
  const actual = provided.startsWith(prefix) ? provided.slice(prefix.length) : provided;
  const left = Buffer.from(expected); const right = Buffer.from(actual);
  return left.length === right.length && timingSafeEqual(left, right);
}

export function verifySlackSignature(rawBody: string | Buffer, secret: string, timestamp: string, provided: string): boolean {
  const parsed = Number(timestamp);
  if (!Number.isInteger(parsed) || Math.abs(Date.now() / 1000 - parsed) > 300) return false;
  return verifyHmacSha256Hex(`v0:${timestamp}:${rawBody}`, secret, provided, "v0=");
}
