<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function telegram_parse_event(array $payload): array
{
    $message = $payload['message'] ?? $payload['edited_message'] ?? [];
    $userId = $message['from']['id'] ?? null; $chatId = $message['chat']['id'] ?? null;
    if ($userId === null || $chatId === null) throw new InvalidArgumentException('Telegram update has no supported message');
    $event = ['platform' => 'telegram', 'user_id' => (string)$userId, 'reply_target' => (string)$chatId];
    if (isset($message['text'])) return $event + ['content_type' => 'text', 'text' => $message['text']];
    if (!empty($message['photo'])) { $photo = end($message['photo']); return $event + ['content_type' => 'image', 'media_url' => 'telegram:'.$photo['file_id']]; }
    foreach ([['audio','audio'], ['video','video'], ['document','file']] as [$key, $type]) if (isset($message[$key])) return $event + ['content_type' => $type, 'media_url' => 'telegram:'.$message[$key]['file_id']];
    throw new InvalidArgumentException('Telegram content type is not supported');
}

function telegram_send_reply(array $event, array $reply, string $token): void
{
    if ($token === '') throw new InvalidArgumentException('TELEGRAM_BOT_TOKEN is required');
    foreach (array_slice($reply['messages'] ?? [], 0, 10) as $message) {
        $type = $message['type'] ?? 'text'; $map = ['image' => ['sendPhoto','photo'], 'audio' => ['sendAudio','audio'], 'video' => ['sendVideo','video'], 'file' => ['sendDocument','document']];
        if ($type === 'text') $body = ['chat_id' => $event['reply_target'] ?? $event['user_id'], 'text' => $message['text'] ?? ''];
        else { if (!isset($map[$type], $message['media_url'])) throw new InvalidArgumentException("Telegram {$type} reply requires media_url"); [$method, $field] = $map[$type]; $body = ['chat_id' => $event['reply_target'] ?? $event['user_id'], $field => preg_replace('/^telegram:/', '', $message['media_url'])]; if (!empty($message['text'])) $body['caption'] = $message['text']; }
        $method ??= 'sendMessage'; $url = 'https://api.telegram.org/bot'.$token.'/'.($method ?? 'sendMessage'); $ch = adapter_curl_init($url); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode($body, JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Telegram API request failed'); curl_close($ch);
    }
}
