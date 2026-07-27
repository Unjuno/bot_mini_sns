<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function google_chat_parse_event(array $payload): array
{
    $message=$payload['message']??$payload;$sender=$message['sender']??[];$space=$payload['space']??[];$user=$sender['name']??$payload['user_id']??'';$room=$space['name']??$payload['space_name']??'';if($user===''||$room==='')throw new InvalidArgumentException('Google Chat event has no sender or space');$attachment=$message['attachments'][0]??$message['attachment'][0]??null;return ['platform'=>'google_chat','user_id'=>(string)$user,'reply_target'=>(string)$room,'content_type'=>$attachment?'file':'text','text'=>$message['text']??null,'media_url'=>$attachment['downloadUri']??$attachment['resourceName']??null];
}
function google_chat_send_reply(array $event,array $reply,string $token):void
{
    if(empty($event['reply_target'])||$token==='')throw new InvalidArgumentException('Google Chat space and token are required');foreach(array_slice($reply['messages']??[],0,5)as$message){$ch=adapter_curl_init('https://chat.googleapis.com/v1/'.$event['reply_target'].'/messages');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode(['text'=>$message['text']??$message['media_url']??''],JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Google Chat API request failed');curl_close($ch);}
}
