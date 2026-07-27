<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function mastodon_parse_event(array $payload): array
{
    $status = $payload['status'] ?? $payload; $userId = $status['account']['id'] ?? $status['user_id'] ?? ''; if ($userId === '') throw new InvalidArgumentException('Mastodon status has no account');
    $media = $status['media_attachments'][0] ?? null; $type = $media ? ($media['type'] ?? 'file') : 'text'; return ['platform' => 'mastodon', 'user_id' => (string)$userId, 'content_type' => in_array($type, ['image','audio','video','file'], true) ? $type : 'text', 'text' => $status['content'] ?? $status['text'] ?? null, 'media_url' => $media['url'] ?? null, 'reply_to_id' => isset($status['id']) ? (string)$status['id'] : null];
}

function mastodon_send_reply(array $event, array $reply, string $baseUrl, string $token): void
{
    if ($baseUrl === '' || $token === '') throw new InvalidArgumentException('Mastodon base URL and token are required'); foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) { if (($message['type'] ?? 'text') !== 'text') throw new InvalidArgumentException('Mastodon media upload is required before media replies'); $ch = curl_init(rtrim($baseUrl, '/').'/api/v1/statuses'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$token, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode(['status' => $message['text'] ?? '', 'in_reply_to_id' => $event['reply_to_id'] ?? null], JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Mastodon API request failed'); curl_close($ch); }
}
