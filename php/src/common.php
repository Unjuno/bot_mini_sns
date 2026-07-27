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
