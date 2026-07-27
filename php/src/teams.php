<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function teams_parse_event(array $payload): array
{
    $user=$payload['from']['id']??$payload['user_id']??'';$conv=$payload['conversation']['id']??'';if($user===''||$conv==='')throw new InvalidArgumentException('Teams activity has no sender or conversation');$attachment=$payload['attachments'][0]??null;return ['platform'=>'teams','user_id'=>(string)$user,'reply_target'=>(string)$conv,'content_type'=>$attachment?'file':'text','text'=>$payload['text']??null,'media_url'=>$attachment['contentUrl']??null];
}
function teams_send_reply(array $event,array $reply,string $serviceUrl,string $token):void
{
    if(empty($event['reply_target'])||$serviceUrl===''||$token==='')throw new InvalidArgumentException('Teams conversation, service URL and token are required');foreach(array_slice($reply['messages']??[],0,5)as$message){$body=['type'=>'message','text'=>$message['text']??$message['media_url']??''];if(($message['type']??'text')!=='text'&&!empty($message['media_url']))$body['attachments']=[['contentType'=>'application/octet-stream','contentUrl'=>$message['media_url'],'name'=>'attachment']];$ch=curl_init(rtrim($serviceUrl,'/').'/v3/conversations/'.rawurlencode((string)$event['reply_target']).'/activities');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Content-Type: application/json'],CURLOPT_POSTFIELDS=>json_encode($body,JSON_THROW_ON_ERROR)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Teams API request failed');curl_close($ch);}
}
