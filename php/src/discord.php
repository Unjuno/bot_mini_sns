<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function discord_parse_event(array $payload): array
{
    $message = $payload['d'] ?? $payload; $userId = $message['author']['id'] ?? ''; $channelId = $message['channel_id'] ?? '';
    if ($userId === '' || $channelId === '') throw new InvalidArgumentException('Discord message has no channel or author');
    $event = ['platform' => 'discord', 'user_id' => (string)$userId, 'reply_target' => (string)$channelId];
    if (!empty($message['content'])) return $event + ['content_type' => 'text', 'text' => $message['content']];
    $attachment = $message['attachments'][0] ?? []; if (empty($attachment['url'])) throw new InvalidArgumentException('Discord message has no supported content');
    $value = strtolower(($attachment['content_type'] ?? '').' '.($attachment['filename'] ?? '')); $type = str_starts_with($value, 'image/') || preg_match('/\.(png|jpe?g|gif|webp)$/', $value) ? 'image' : (str_starts_with($value, 'audio/') ? 'audio' : (str_starts_with($value, 'video/') ? 'video' : 'file'));
    return $event + ['content_type' => $type, 'media_url' => $attachment['url']];
}

function discord_send_reply(array $event, array $reply, string $token): void
{
    $channel = $event['reply_target'] ?? ''; if ($channel === '' || $token === '') throw new InvalidArgumentException('Discord channel and token are required');
    foreach (array_slice($reply['messages'] ?? [], 0, 10) as $message) {
        $body = ['content' => mb_substr((string)($message['text'] ?? ''), 0, 2000), 'allowed_mentions' => ['parse' => []]];
        $ch = adapter_curl_init('https://discord.com/api/v10/channels/'.rawurlencode((string)$channel).'/messages'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bot '.$token, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode($body, JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Discord API request failed'); curl_close($ch);
    }
}
