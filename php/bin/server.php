<?php

declare(strict_types=1);

require __DIR__ . '/../src/common.php';
foreach (glob(__DIR__.'/../src/{platforms,telegram,discord,mastodon,misskey,bluesky,slack,matrix,whatsapp,viber,zulip,google_chat,teams,instagram,reddit,twitch,kakaotalk}.php', GLOB_BRACE) as $adapterFile) {
    require_once $adapterFile;
}

$storePath = getenv('PHP_POSTS_FILE') ?: (__DIR__ . '/posts.json');
$posts = [];
if (is_file($storePath)) {
    $stored = json_decode((string) file_get_contents($storePath), true);
    if (is_array($stored)) {
        $posts = $stored;
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'POST required'], JSON_THROW_ON_ERROR);
    exit;
}

try {
    $payload = json_decode(file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    [$event, $sendReply] = runtime_adapter($payload);
    $reply = process_event($event, $posts, 5);
    $directory = dirname($storePath);
    if (!is_dir($directory)) {
        mkdir($directory, 0775, true);
    }
    file_put_contents($storePath, json_encode($posts, JSON_THROW_ON_ERROR), LOCK_EX);
    if ($sendReply !== null) {
        $sendReply($event, $reply);
    }
    header('Content-Type: application/json');
    echo json_encode($reply, JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    http_response_code(400);
    header('Content-Type: application/json');
    echo json_encode(['error' => $error->getMessage()], JSON_THROW_ON_ERROR);
}

/** @return array{0: array<string,mixed>, 1: ?Closure} */
function runtime_adapter(array $payload): array
{
    return match (strtolower(trim((string) (getenv('PLATFORM') ?: '')))) {
        'line' => (function () use ($payload): array { $event = line_parse_event($payload); return [$event, fn(array $event, array $reply): null => line_send_reply($event, $reply, (string) getenv('ACCESS_TOKEN'))]; })(),
        'telegram' => (function () use ($payload): array { $event = telegram_parse_event($payload); return [$event, fn(array $event, array $reply): null => telegram_send_reply($event, $reply, (string) getenv('TELEGRAM_BOT_TOKEN'))]; })(),
        'discord' => (function () use ($payload): array { $event = discord_parse_event($payload); return [$event, fn(array $event, array $reply): null => discord_send_reply($event, $reply, (string) getenv('DISCORD_BOT_TOKEN'))]; })(),
        'kakaotalk' => (function () use ($payload): array { return [kakaotalk_parse_event($payload), null]; })(),
        default => [$payload, null],
    };
}
