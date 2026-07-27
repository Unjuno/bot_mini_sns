<?php

declare(strict_types=1);

foreach (glob(__DIR__.'/../src/{http,platforms,telegram,discord,mastodon,misskey,bluesky,slack,matrix,whatsapp,viber,zulip,google_chat,teams,instagram,reddit,twitch,kakaotalk}.php', GLOB_BRACE) as $file) require_once $file;

$reply = ['messages' => [['type' => 'text', 'text' => 'mock']]];
$cases = [
    'line' => fn() => line_send_reply(['reply_token' => 'r'], $reply, 'token'),
    'telegram' => fn() => telegram_send_reply(['chat_id' => 'c', 'user_id' => 'u'], $reply, 'token'),
    'discord' => fn() => discord_send_reply(['reply_target' => 'c'], $reply, 'token'),
    'mastodon' => fn() => mastodon_send_reply(['reply_to_id' => 's'], $reply, 'http://mock', 'token'),
    'misskey' => fn() => misskey_send_reply(['reply_to_id' => 'n'], $reply, 'http://mock', 'token'),
    'bluesky' => fn() => bluesky_send_reply([], $reply, 'http://mock', 'jwt', 'repo'),
    'slack' => fn() => slack_send_reply(['reply_target' => 'c', 'user_id' => 'u'], $reply, 'token'),
    'matrix' => fn() => matrix_send_reply(['reply_target' => '!r'], $reply, 'http://mock', 'token'),
    'whatsapp' => fn() => whatsapp_send_reply(['user_id' => 'u'], $reply, 'phone', 'token'),
    'viber' => fn() => viber_send_reply(['user_id' => 'u'], $reply, 'token'),
    'zulip' => fn() => zulip_send_reply(['user_id' => 'u'], $reply, 'http://mock', 'user@example.com', 'key'),
    'google_chat' => fn() => google_chat_send_reply(['reply_target' => 'spaces/1'], $reply, 'token'),
    'teams' => fn() => teams_send_reply(['reply_target' => 'c'], $reply, 'http://mock', 'token'),
    'instagram' => fn() => instagram_send_reply(['user_id' => 'u'], $reply, 'account', 'token'),
    'reddit' => fn() => reddit_send_reply(['media_url' => 't1_x'], $reply, 'token'),
    'twitch' => fn() => twitch_send_reply([], $reply, 'token', 'client', 'broadcaster', 'sender'),
];

foreach ($cases as $platform => $send) {
    try { $send(); } catch (Throwable $error) { throw new RuntimeException($platform.' send failed: '.$error->getMessage(), 0, $error); }
}
if (kakaotalk_render_reply($reply)['version'] !== '2.0') throw new RuntimeException('KakaoTalk render failed');
echo 'ok '.count($cases).' send adapters and KakaoTalk render'.PHP_EOL;
