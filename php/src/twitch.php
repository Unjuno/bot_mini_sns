<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function twitch_parse_event(array $payload): array
{
    $event=$payload['event']??$payload;$user=$event['chatter_user_id']??$event['user_id']??'';$text=is_array($event['message']??null)?($event['message']['text']??null):($event['message']??$event['text']??null);if($user===''||$text===null)throw new InvalidArgumentException('Twitch event has no chat message');return ['platform'=>'twitch','user_id'=>(string)$user,'content_type'=>'text','text'=>(string)$text,'reply_to_id'=>$event['message_id']??null];
}
function twitch_send_reply(array $event,array $reply,string $token,string $clientId,string $broadcasterId,string $senderId):void
{
    if($token===''||$clientId===''||$broadcasterId===''||$senderId==='')throw new InvalidArgumentException('Twitch credentials are required');foreach(array_slice($reply['messages']??[],0,5)as$message){if(($message['type']??'text')!=='text')throw new InvalidArgumentException('Twitch chat supports text replies only');$body=['broadcaster_id'=>$broadcasterId,'sender_id'=>$senderId,'message'=>$message['text']??''];if(!empty($event['reply_to_id']))$body['reply_parent_message_id']=$event['reply_to_id'];$ch=curl_init('https://api.twitch.tv/helix/chat/messages');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Client-Id: '.$clientId,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($body,JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);$bodyResult=is_string($result)?json_decode($result,true):null;if($result===false||$status<200||$status>=300||empty($bodyResult['data'][0]['is_sent']))throw new RuntimeException('Twitch API request failed');curl_close($ch);}
}
