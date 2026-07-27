<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function whatsapp_parse_event(array $payload): array
{
    $value = $payload['entry'][0]['changes'][0]['value'] ?? $payload; $message = $value['messages'][0] ?? $payload['message'] ?? []; $user = $message['from'] ?? ''; if ($user === '') throw new InvalidArgumentException('WhatsApp webhook has no sender'); $raw = $message['type'] ?? 'text'; $type = $raw === 'document' ? 'file' : $raw; $item = $message[$raw === 'document' ? 'document' : $raw] ?? []; return ['platform'=>'whatsapp','user_id'=>(string)$user,'content_type'=>$type,'text'=>$item['body'] ?? $item['caption'] ?? null,'media_url'=>$item['id'] ?? null];
}
function whatsapp_send_reply(array $event, array $reply, string $phoneNumberId, string $token): void
{
    if ($phoneNumberId === '' || $token === '') throw new InvalidArgumentException('WhatsApp phone number ID and token are required'); foreach (array_slice($reply['messages'] ?? [],0,5) as $message) { $type = ($message['type'] ?? 'text') === 'file' ? 'document' : ($message['type'] ?? 'text'); $body = ['messaging_product'=>'whatsapp','to'=>$event['user_id'],'type'=>$type]; if ($type === 'text') $body['text']=['body'=>$message['text'] ?? '']; else { if (empty($message['media_url'])) throw new InvalidArgumentException('WhatsApp media reply requires media ID'); $body[$type]=['id'=>$message['media_url']]; } $ch=adapter_curl_init('https://graph.facebook.com/v20.0/'.$phoneNumberId.'/messages');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($body,JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('WhatsApp API request failed');curl_close($ch); }
}
