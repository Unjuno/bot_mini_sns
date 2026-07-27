<?php

declare(strict_types=1);

function misskey_content_type(string $mime): string { return str_starts_with($mime, 'image/') ? 'image' : (str_starts_with($mime, 'audio/') ? 'audio' : (str_starts_with($mime, 'video/') ? 'video' : 'file')); }
/** @return array<string,mixed> */
function misskey_parse_event(array $payload): array
{
    $note = $payload['note'] ?? $payload; $userId = $note['userId'] ?? $note['user']['id'] ?? ''; if ($userId === '') throw new InvalidArgumentException('Misskey note has no user'); $file = $note['files'][0] ?? null; return ['platform' => 'misskey', 'user_id' => (string)$userId, 'content_type' => $file ? misskey_content_type((string)($file['type'] ?? '')) : 'text', 'text' => $note['text'] ?? null, 'media_url' => $file['id'] ?? null, 'reply_to_id' => isset($note['id']) ? (string)$note['id'] : null];
}
function misskey_send_reply(array $event, array $reply, string $baseUrl, string $token): void
{
    if ($baseUrl === '' || $token === '') throw new InvalidArgumentException('Misskey base URL and token are required'); foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) { $body = ['i' => $token, 'text' => $message['text'] ?? '', 'replyId' => $event['reply_to_id'] ?? null]; if (($message['type'] ?? 'text') !== 'text') { if (empty($message['media_url'])) throw new InvalidArgumentException('Misskey media reply requires file ID'); $body['fileIds'] = [$message['media_url']]; } $ch = curl_init(rtrim($baseUrl, '/').'/api/notes/create'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode($body, JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Misskey API request failed'); curl_close($ch); }
}
