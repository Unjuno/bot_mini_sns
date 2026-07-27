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

/** Persistent SQLite implementation used by the standalone PHP webhook. */
function process_event_sqlite(PDO $database, array $event, int $limit = 5): array
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
    if ($limit < 1) throw new InvalidArgumentException('limit must be a positive integer');

    $database->beginTransaction();
    try {
        $insert = $database->prepare('INSERT INTO platform_posts (platform, user_id, content_type, text, media_url, created_at) VALUES (:platform, :user_id, :content_type, :text, :media_url, :created_at)');
        $insert->execute([
            ':platform' => $event['platform'], ':user_id' => $event['user_id'],
            ':content_type' => $event['content_type'], ':text' => $event['text'] ?? null,
            ':media_url' => $event['media_url'] ?? null, ':created_at' => gmdate('c'),
        ]);
        $select = $database->prepare('SELECT content_type, text, media_url FROM platform_posts WHERE content_type = :content_type ORDER BY id DESC LIMIT :limit');
        $select->bindValue(':content_type', $event['content_type'], PDO::PARAM_STR);
        $select->bindValue(':limit', $limit, PDO::PARAM_INT);
        $select->execute();
        $messages = [];
        foreach ($select->fetchAll(PDO::FETCH_ASSOC) as $post) {
            $messages[] = ['type' => $post['content_type'], 'text' => $post['text'] ?? '', 'media_url' => $post['media_url']];
        }
        $database->commit();
        return ['messages' => $messages];
    } catch (Throwable $error) {
        $database->rollBack();
        throw $error;
    }
}
