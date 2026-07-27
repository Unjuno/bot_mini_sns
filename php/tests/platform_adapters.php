<?php

declare(strict_types=1);

foreach (glob(__DIR__.'/../src/{platforms,telegram,discord,mastodon,misskey,bluesky,slack,matrix,whatsapp,viber,zulip,google_chat,teams,instagram,reddit,twitch,kakaotalk}.php', GLOB_BRACE) as $file) require_once $file;
require_once __DIR__.'/../src/security.php';

$cases = [
    'line' => fn() => line_parse_event(['events' => [['source' => ['userId' => 'u'], 'message' => ['type' => 'text', 'text' => 'x']]]]),
    'telegram' => fn() => telegram_parse_event(['message' => ['from' => ['id' => 1], 'chat' => ['id' => 2], 'text' => 'x']]),
    'discord' => fn() => discord_parse_event(['d' => ['channel_id' => 'c', 'author' => ['id' => 'u'], 'content' => 'x']]),
    'mastodon' => fn() => mastodon_parse_event(['account' => ['id' => 'u'], 'id' => 's', 'content' => 'x']),
    'misskey' => fn() => misskey_parse_event(['id' => 'n', 'userId' => 'u', 'text' => 'x']),
    'bluesky' => fn() => bluesky_parse_event(['author' => 'did:u', 'record' => ['text' => 'x']]),
    'slack' => fn() => slack_parse_event(['event' => ['user' => 'u', 'channel' => 'c', 'text' => 'x']]),
    'matrix' => fn() => matrix_parse_event(['event' => ['sender' => '@u:test', 'room_id' => '!r:test', 'content' => ['msgtype' => 'm.text', 'body' => 'x']]]),
    'whatsapp' => fn() => whatsapp_parse_event(['entry' => [['changes' => [['value' => ['messages' => [['from' => 'u', 'type' => 'text', 'text' => ['body' => 'x']]]]]]]]]),
    'viber' => fn() => viber_parse_event(['sender' => ['id' => 'u'], 'message' => ['type' => 'text', 'text' => 'x']]),
    'zulip' => fn() => zulip_parse_event(['message' => ['sender_email' => 'u@test', 'content' => 'x']]),
    'google_chat' => fn() => google_chat_parse_event(['space' => ['name' => 'spaces/1'], 'message' => ['sender' => ['name' => 'users/1'], 'text' => 'x']]),
    'teams' => fn() => teams_parse_event(['from' => ['id' => 'u'], 'conversation' => ['id' => 'c'], 'text' => 'x']),
    'instagram' => fn() => instagram_parse_event(['entry' => [['messaging' => [['sender' => ['id' => 'u'], 'message' => ['text' => 'x']]]]]]),
    'reddit' => fn() => reddit_parse_event(['data' => ['author' => ['name' => 'u'], 'body' => 'x', 'name' => 't1_x']]),
    'twitch' => fn() => twitch_parse_event(['event' => ['chatter_user_id' => 'u', 'message_id' => 'm', 'message' => 'x']]),
    'kakaotalk' => fn() => kakaotalk_parse_event(['userRequest' => ['user' => ['id' => 'u'], 'utterance' => 'x']]),
];

foreach ($cases as $platform => $parse) {
    $event = $parse();
    if (($event['platform'] ?? '') !== $platform || ($event['content_type'] ?? '') !== 'text') throw new RuntimeException("{$platform} contract failed: ".json_encode($event));
}
echo 'ok '.count($cases)." adapters\n";

$signedBody = '{"events":[]}';
$base64Signature = base64_encode(hash_hmac('sha256', $signedBody, 'secret', true));
if (!verify_hmac_sha256($signedBody, 'secret', 'Bearer '.$base64Signature, 'Bearer ')) throw new RuntimeException('base64 signature contract failed');
if (verify_hmac_sha256($signedBody, 'secret', 'Bearer invalid', 'Bearer ')) throw new RuntimeException('invalid base64 signature accepted');
$hexSignature = hash_hmac('sha256', 'v0:123:'.$signedBody, 'secret');
if (!verify_slack_signature($signedBody, 'secret', '123', 'v0='.$hexSignature)) throw new RuntimeException('Slack signature contract failed');
if (verify_slack_signature($signedBody, 'secret', '123', 'v0=invalid')) throw new RuntimeException('invalid Slack signature accepted');
echo "ok webhook signatures\n";
