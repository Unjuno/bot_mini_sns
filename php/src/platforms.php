<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function line_parse_event(array $payload): array
{
    $event = $payload['events'][0] ?? $payload;
    $message = $event['message'] ?? [];
    $source = $event['source'] ?? [];
    $userId = $source['userId'] ?? $payload['user_id'] ?? '';
    if ($userId === '') throw new InvalidArgumentException('LINE event has no userId');
    $type = $message['type'] ?? 'text';
    if ($type === 'document') $type = 'file';
    return ['platform' => 'line', 'user_id' => (string)$userId, 'content_type' => $type, 'text' => $message['text'] ?? null, 'media_url' => $message['id'] ?? null, 'reply_token' => $event['replyToken'] ?? null];
}

function line_send_reply(array $event, array $reply, string $accessToken): void
{
    $token = $event['reply_token'] ?? '';
    if ($accessToken === '' || $token === '') throw new InvalidArgumentException('LINE access token and reply token are required');
    $messages = [];
    foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) {
        $type = $message['type'] ?? 'text';
        if ($type === 'text') $messages[] = ['type' => 'text', 'text' => $message['text'] ?: ($message['media_url'] ?? '')];
        else {
            $url = $message['media_url'] ?? '';
            if ($url === '') throw new InvalidArgumentException("LINE {$type} reply requires media_url");
            $item = ['type' => $type, 'originalContentUrl' => $url, 'previewImageUrl' => $url];
            if ($type === 'audio') $item = ['type' => 'audio', 'originalContentUrl' => $url, 'duration' => 1000];
            if ($type === 'file') $item['fileName'] = $message['text'] ?: 'attachment';
            $messages[] = $item;
        }
    }
    $ch = curl_init('https://api.line.me/v2/bot/message/reply');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$accessToken, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode(['replyToken' => $token, 'messages' => $messages], JSON_THROW_ON_ERROR)]);
    $response = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($response === false || $status < 200 || $status >= 300) throw new RuntimeException('LINE API request failed'); curl_close($ch);
}
