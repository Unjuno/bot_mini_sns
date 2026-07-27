<?php

declare(strict_types=1);

/** @return list<string> */
function supported_platforms(): array
{
    return ['line', 'telegram', 'discord', 'zulip', 'matrix', 'slack', 'google_chat',
        'viber', 'mastodon', 'misskey', 'bluesky', 'whatsapp', 'instagram', 'teams',
        'kakaotalk', 'twitch', 'reddit'];
}

function process_event(array $event, array &$posts, int $limit = 5): array
{
    if (!in_array($event['platform'] ?? '', supported_platforms(), true)) {
        throw new InvalidArgumentException('Unsupported platform');
    }
    if (($event['user_id'] ?? '') === '' || ($event['content_type'] ?? '') === '') {
        throw new InvalidArgumentException('platform, user_id, and content_type are required');
    }
    if (!in_array($event['content_type'], ['text', 'image', 'audio', 'video', 'file'], true)) {
        throw new InvalidArgumentException('Unsupported content type');
    }
    if ($limit < 1) {
        throw new InvalidArgumentException('limit must be a positive integer');
    }
    $posts[] = $event;
    $selected = [];
    for ($i = count($posts) - 1; $i >= 0 && count($selected) < $limit; $i--) {
        $post = $posts[$i];
        if ($post['content_type'] === $event['content_type']) {
            $selected[] = [
                'type' => $post['content_type'],
                'text' => $post['text'] ?? '',
                'media_url' => $post['media_url'] ?? null,
            ];
        }
    }
    return ['messages' => $selected];
}
