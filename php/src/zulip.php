<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function zulip_parse_event(array $payload): array
{
    $message=$payload['message']??$payload;$user=$message['sender_email']??$message['sender_id']??'';if($user==='')throw new InvalidArgumentException('Zulip message has no sender');if(($message['type']??'')==='stream'){if(empty($message['display_recipient'])||empty($message['subject']))throw new InvalidArgumentException('Zulip stream message has no stream or subject');return ['platform'=>'zulip','user_id'=>(string)$user,'reply_target'=>(string)$message['display_recipient'],'reply_to_id'=>(string)$message['subject'],'reply_mode'=>'stream','content_type'=>'text','text'=>$message['content']??$message['text']??null];}return ['platform'=>'zulip','user_id'=>(string)$user,'reply_mode'=>'direct','content_type'=>'text','text'=>$message['content']??$message['text']??null];
}
function zulip_send_reply(array $event,array $reply,string $baseUrl,string $email,string $apiKey):void
{
    if($baseUrl===''||$email===''||$apiKey==='')throw new InvalidArgumentException('Zulip base URL, email and API key are required');foreach(array_slice($reply['messages']??[],0,5)as$message){$form=['type'=>($event['reply_mode']??'direct')==='stream'?'stream':'direct','to'=>($event['reply_mode']??'direct')==='stream'?$event['reply_target']:$event['user_id'],'content'=>$message['text']??$message['media_url']??''];if(($event['reply_mode']??'')==='stream')$form['subject']=$event['reply_to_id'];$ch=adapter_curl_init(rtrim($baseUrl,'/').'/api/v1/messages');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_USERPWD=>$email.':'.$apiKey,CURLOPT_HTTPAUTH=>CURLAUTH_BASIC,CURLOPT_POSTFIELDS=>http_build_query($form)]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);if($result===false||$status<200||$status>=300)throw new RuntimeException('Zulip API request failed');curl_close($ch);}
}
