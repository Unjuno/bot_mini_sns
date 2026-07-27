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
    $rawBody = file_get_contents('php://input');
    if (strtolower(trim((string) (getenv('PLATFORM') ?: ''))) === 'line' && !verify_hmac_sha256($rawBody, (string) getenv('CHANNEL_SECRET'), (string) ($_SERVER['HTTP_X_LINE_SIGNATURE'] ?? ''))) {
        http_response_code(401);
        throw new RuntimeException('invalid LINE signature');
    }
    $payload = json_decode($rawBody, true, 512, JSON_THROW_ON_ERROR);
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
    $response = strtolower(trim((string) (getenv('PLATFORM') ?: ''))) === 'kakaotalk'
        ? kakaotalk_render_reply($reply)
        : $reply;
    echo json_encode($response, JSON_THROW_ON_ERROR);
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
        'mastodon' => (function () use ($payload): array { $event = mastodon_parse_event($payload); return [$event, fn(array $event, array $reply): null => mastodon_send_reply($event, $reply, (string) getenv('MASTODON_BASE_URL'), (string) getenv('MASTODON_ACCESS_TOKEN'))]; })(),
        'misskey' => (function () use ($payload): array { $event = misskey_parse_event($payload); return [$event, fn(array $event, array $reply): null => misskey_send_reply($event, $reply, (string) getenv('MISSKEY_BASE_URL'), (string) getenv('MISSKEY_TOKEN'))]; })(),
        'bluesky' => (function () use ($payload): array { $event = bluesky_parse_event($payload); return [$event, fn(array $event, array $reply): null => bluesky_send_reply($event, $reply, (string) (getenv('BLUESKY_SERVICE_URL') ?: 'https://bsky.social'), (string) getenv('BLUESKY_ACCESS_JWT'), (string) getenv('BLUESKY_REPO'))]; })(),
        'slack' => (function () use ($payload): array { $event = slack_parse_event($payload); return [$event, fn(array $event, array $reply): null => slack_send_reply($event, $reply, (string) getenv('SLACK_BOT_TOKEN'))]; })(),
        'matrix' => (function () use ($payload): array { $event = matrix_parse_event($payload); return [$event, fn(array $event, array $reply): null => matrix_send_reply($event, $reply, (string) getenv('MATRIX_BASE_URL'), (string) getenv('MATRIX_ACCESS_TOKEN'))]; })(),
        'whatsapp' => (function () use ($payload): array { $event = whatsapp_parse_event($payload); return [$event, fn(array $event, array $reply): null => whatsapp_send_reply($event, $reply, (string) getenv('WHATSAPP_PHONE_NUMBER_ID'), (string) getenv('WHATSAPP_ACCESS_TOKEN'))]; })(),
        'viber' => (function () use ($payload): array { $event = viber_parse_event($payload); return [$event, fn(array $event, array $reply): null => viber_send_reply($event, $reply, (string) getenv('VIBER_AUTH_TOKEN'))]; })(),
        'zulip' => (function () use ($payload): array { $event = zulip_parse_event($payload); return [$event, fn(array $event, array $reply): null => zulip_send_reply($event, $reply, (string) getenv('ZULIP_BASE_URL'), (string) getenv('ZULIP_EMAIL'), (string) getenv('ZULIP_API_KEY'))]; })(),
        'google_chat' => (function () use ($payload): array { $event = google_chat_parse_event($payload); return [$event, fn(array $event, array $reply): null => google_chat_send_reply($event, $reply, (string) getenv('GOOGLE_CHAT_ACCESS_TOKEN'))]; })(),
        'teams' => (function () use ($payload): array { $event = teams_parse_event($payload); return [$event, fn(array $event, array $reply): null => teams_send_reply($event, $reply, (string) getenv('TEAMS_SERVICE_URL'), (string) getenv('TEAMS_BOT_TOKEN'))]; })(),
        'instagram' => (function () use ($payload): array { $event = instagram_parse_event($payload); return [$event, fn(array $event, array $reply): null => instagram_send_reply($event, $reply, (string) getenv('INSTAGRAM_ACCOUNT_ID'), (string) getenv('INSTAGRAM_ACCESS_TOKEN'))]; })(),
        'reddit' => (function () use ($payload): array { $event = reddit_parse_event($payload); return [$event, fn(array $event, array $reply): null => reddit_send_reply($event, $reply, (string) getenv('REDDIT_ACCESS_TOKEN'))]; })(),
        'twitch' => (function () use ($payload): array { $event = twitch_parse_event($payload); return [$event, fn(array $event, array $reply): null => twitch_send_reply($event, $reply, (string) getenv('TWITCH_ACCESS_TOKEN'), (string) getenv('TWITCH_CLIENT_ID'), (string) getenv('TWITCH_BROADCASTER_ID'), (string) getenv('TWITCH_SENDER_ID'))]; })(),
        'kakaotalk' => (function () use ($payload): array { return [kakaotalk_parse_event($payload), null]; })(),
        default => [$payload, null],
    };
}
