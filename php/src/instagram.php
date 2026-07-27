<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function instagram_parse_event(array $payload): array
{
    $event=$payload['entry'][0]['messaging'][0]??$payload;$message=$event['message']??$payload['message']??[];$sender=$event['sender']??$payload['sender']??[];$user=$sender['id']??'';if($user==='')throw new InvalidArgumentException('Instagram event has no sender');if(array_key_exists('text',$message))return ['platform'=>'instagram','user_id'=>(string)$user,'content_type'=>'text','text'=>$message['text']];$attachment=$message['attachments'][0]??null;if(!$attachment)throw new InvalidArgumentException('Instagram event has no supported message');$type=in_array($attachment['type']??'', ['image','audio','video','file'], true)?$attachment['type']:'file';return ['platform'=>'instagram','user_id'=>(string)$user,'content_type'=>$type,'media_url'=>$attachment['payload']['url']??null];
}
function instagram_send_reply(array $event,array $reply,string $accountId,string $token):void
{
    if($accountId===''||$token==='')throw new InvalidArgumentException('Instagram account ID and token are required');foreach(array_slice($reply['messages']??[],0,5)as$message){$body=['recipient'=>['id'=>$event['user_id']]];if(($message['type']??'text')==='text')$body['message']=['text'=>$message['text']??''];else{$url=$message['media_url']??'';if($url==='')throw new InvalidArgumentException('Instagram media reply requires URL');$body['message']=['attachment'=>['type'=>$message['type'],'payload'=>['url'=>$url]]];}$ch=adapter_curl_init('https://graph.facebook.com/v20.0/'.$accountId.'/messages');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($body,JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Instagram API request failed');curl_close($ch);}
}
