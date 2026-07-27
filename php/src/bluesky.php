<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function bluesky_parse_event(array $payload): array
{
    $record = $payload['record'] ?? $payload; $author = $payload['author'] ?? $payload['did'] ?? ''; if ($author === '' || !array_key_exists('text', $record)) throw new InvalidArgumentException('Bluesky post has no supported content'); return ['platform' => 'bluesky', 'user_id' => (string)$author, 'content_type' => 'text', 'text' => $record['text'], 'reply_to_uri' => $payload['uri'] ?? null, 'reply_to_cid' => $payload['cid'] ?? null];
}
function bluesky_send_reply(array $event, array $reply, string $serviceUrl, string $jwt, string $repo): void
{
    if ($serviceUrl === '' || $jwt === '' || $repo === '') throw new InvalidArgumentException('Bluesky service URL, JWT and repo are required'); foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) { if (($message['type'] ?? 'text') !== 'text') throw new InvalidArgumentException('Bluesky Blob upload is required before media replies'); $record = ['$type' => 'app.bsky.feed.post', 'text' => $message['text'] ?? '', 'createdAt' => gmdate('Y-m-d\TH:i:s.v\Z')]; if (!empty($event['reply_to_uri']) && !empty($event['reply_to_cid'])) $record['reply'] = ['root' => ['uri' => $event['reply_to_uri'], 'cid' => $event['reply_to_cid']], 'parent' => ['uri' => $event['reply_to_uri'], 'cid' => $event['reply_to_cid']]]; $ch = adapter_curl_init(rtrim($serviceUrl, '/').'/xrpc/com.atproto.repo.createRecord'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$jwt, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode(['repo' => $repo, 'collection' => 'app.bsky.feed.post', 'record' => $record], JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Bluesky API request failed'); curl_close($ch); }
}
