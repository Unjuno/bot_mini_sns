<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function viber_parse_event(array $payload): array
{
    $sender = $payload['sender'] ?? []; $message = $payload['message'] ?? []; $user = $sender['id'] ?? ''; if ($user === '') throw new InvalidArgumentException('Viber event has no sender'); $type = $message['type'] ?? 'text'; return ['platform'=>'viber','user_id'=>(string)$user,'content_type'=>$type,'text'=>$message['text'] ?? null,'media_url'=>$message['media'] ?? null];
}
function viber_send_reply(array $event, array $reply, string $token): void
{
    if ($token === '') throw new InvalidArgumentException('VIBER_AUTH_TOKEN is required'); foreach (array_slice($reply['messages'] ?? [],0,5) as $message) { $type=$message['type'] ?? 'text'; if ($type==='audio') throw new InvalidArgumentException('Viber audio replies are not supported'); $body=['receiver'=>$event['user_id'],'type'=>$type]; if($type==='text')$body['text']=$message['text']??'';else{$body['media']=$message['media_url']??'';if($body['media']==='')throw new InvalidArgumentException('Viber media reply requires URL');if(!empty($message['text']))$body['text']=$message['text'];}$ch=curl_init('https://chatapi.viber.com/pa/send_message');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['X-Viber-Auth-Token: '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($body,JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Viber API request failed');curl_close($ch);}
}
