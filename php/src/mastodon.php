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
    if ($baseUrl === '' || $token === '') throw new InvalidArgumentException('Mastodon base URL and token are required');
    foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) {
        $mediaId = null;
        if (($message['type'] ?? 'text') !== 'text') {
            $mediaUrl = (string)($message['media_url'] ?? '');
            if ($mediaUrl === '') throw new InvalidArgumentException('Mastodon media reply requires URL');
            $download = adapter_curl_init($mediaUrl);
            curl_setopt_array($download, [CURLOPT_RETURNTRANSFER => true]);
            $bytes = curl_exec($download); $downloadStatus = curl_getinfo($download, CURLINFO_RESPONSE_CODE); curl_close($download);
            if ($bytes === false || $downloadStatus < 200 || $downloadStatus >= 300) throw new RuntimeException('Mastodon media download failed');
            $tmp = tempnam(sys_get_temp_dir(), 'mastodon-'); if ($tmp === false || file_put_contents($tmp, $bytes) === false) throw new RuntimeException('Unable to stage Mastodon media');
            try {
                $upload = adapter_curl_init(rtrim($baseUrl, '/').'/api/v2/media');
                curl_setopt_array($upload, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$token], CURLOPT_POSTFIELDS => ['file' => new CURLFile($tmp, 'application/octet-stream', 'reply.'.($message['type'] ?? 'file'))]]);
                $raw = curl_exec($upload); $uploadStatus = curl_getinfo($upload, CURLINFO_RESPONSE_CODE); curl_close($upload);
                if ($raw === false || $uploadStatus < 200 || $uploadStatus >= 300) throw new RuntimeException('Mastodon media upload failed');
                $uploaded = json_decode($raw, true, 512, JSON_THROW_ON_ERROR); $mediaId = $uploaded['id'] ?? null;
                if (!is_string($mediaId) || $mediaId === '') throw new RuntimeException('Mastodon media upload returned no ID');
            } finally { @unlink($tmp); }
        }
        $body = ['status' => $message['text'] ?? '', 'in_reply_to_id' => $event['reply_to_id'] ?? null]; if ($mediaId !== null) $body['media_ids'] = [$mediaId];
        $ch = adapter_curl_init(rtrim($baseUrl, '/').'/api/v1/statuses'); curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$token, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode($body, JSON_THROW_ON_ERROR)]); $result = curl_exec($ch); $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE); curl_close($ch); if ($result === false || $status < 200 || $status >= 300) throw new RuntimeException('Mastodon API request failed');
    }
}
