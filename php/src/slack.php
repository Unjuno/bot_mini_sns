<?php

declare(strict_types=1);

function slack_content_type(string $mime, string $name): string { $value = strtolower($mime.' '.$name); return str_starts_with($value, 'image/') ? 'image' : (str_starts_with($value, 'audio/') ? 'audio' : (str_starts_with($value, 'video/') ? 'video' : 'file')); }
/** @return array<string,mixed> */
function slack_parse_event(array $payload): array
{
    $event = $payload['event'] ?? $payload; $userId = $event['user'] ?? $event['user_id'] ?? ''; $channelId = $event['channel'] ?? $event['channel_id'] ?? ''; if ($userId === '' || $channelId === '') throw new InvalidArgumentException('Slack event has no user or channel'); $file = $event['files'][0] ?? null; return ['platform' => 'slack', 'user_id' => (string)$userId, 'reply_target' => (string)$channelId, 'content_type' => $file ? slack_content_type((string)($file['mimetype'] ?? ''), (string)($file['name'] ?? '')) : 'text', 'text' => $event['text'] ?? null, 'media_url' => $file['url_private'] ?? null];
}
function slack_send_reply(array $event, array $reply, string $token): void
{
    if ($token === '') throw new InvalidArgumentException('SLACK_BOT_TOKEN is required'); foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) { $ch = curl_init('https://slack.com/api/chat.postMessage'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$token, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode(['channel' => $event['reply_target'] ?? $event['user_id'], 'text' => $message['text'] ?? $message['media_url'] ?? ''], JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); $body = is_string($result) ? json_decode($result, true) : null; if ($result === false || $status < 200 || $status >= 300 || (($body['ok'] ?? false) !== true)) throw new RuntimeException('Slack API request failed: '.($body['error'] ?? 'unknown')); curl_close($ch); }
}
