<?php

declare(strict_types=1);

function process_event(array $event, array &$posts, int $limit = 5): array
{
    $posts[] = $event;
    $selected = [];
    for ($i = count($posts) - 1; $i >= 0 && count($selected) < $limit; $i--) {
        $post = $posts[$i];
        if ($post['platform'] === $event['platform']
            && $post['user_id'] === $event['user_id']
            && $post['content_type'] === $event['content_type']) {
            $selected[] = [
                'type' => $post['content_type'],
                'text' => $post['text'] ?? '',
                'media_url' => $post['media_url'] ?? null,
            ];
        }
    }
    return ['messages' => $selected];
}
