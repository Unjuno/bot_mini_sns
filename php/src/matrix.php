<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function matrix_parse_event(array $payload): array
{
    $event = $payload['event'] ?? $payload; $content = $event['content'] ?? $event; $room = $event['room_id'] ?? $payload['room_id'] ?? ''; if ($room === '') throw new InvalidArgumentException('Matrix event has no room_id'); $kind = ['m.image'=>'image','m.audio'=>'audio','m.video'=>'video','m.file'=>'file'][$content['msgtype'] ?? ''] ?? 'text'; return ['platform'=>'matrix','user_id'=>(string)($event['sender'] ?? $payload['user_id'] ?? ''),'reply_target'=>(string)$room,'content_type'=>$kind,'text'=>$content['body'] ?? null,'media_url'=>$content['url'] ?? null];
}
function matrix_send_reply(array $event, array $reply, string $baseUrl, string $token): void
{
    if (empty($event['reply_target']) || $baseUrl === '' || $token === '') throw new InvalidArgumentException('Matrix room, base URL and token are required'); foreach (array_slice($reply['messages'] ?? [], 0, 5) as $message) { $content = ($message['type'] ?? 'text') === 'text' ? ['msgtype'=>'m.text','body'=>$message['text'] ?? ''] : ['msgtype'=>'m.'.($message['type'] ?? 'file'),'body'=>$message['text'] ?? $message['media_url'] ?? '','url'=>$message['media_url'] ?? null]; $txn = 'bot-'.bin2hex(random_bytes(8)); $ch = curl_init(rtrim($baseUrl,'').'/_matrix/client/v3/rooms/'.rawurlencode((string)$event['reply_target']).'/send/m.room.message/'.$txn); curl_setopt_array($ch,[CURLOPT_CUSTOMREQUEST=>'PUT',CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($content,JSON_THROW_ON_ERROR)]); $result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Matrix API request failed');curl_close($ch); }
}
