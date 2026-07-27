<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function reddit_parse_event(array $payload): array
{
    $data=$payload['data']??$payload;$author=is_array($data['author']??null)?($data['author']['name']??''):($data['author']??'');$thing=$data['name']??$data['id']??'';if($author===''||$thing==='')throw new InvalidArgumentException('Reddit event has no author or thing ID');return ['platform'=>'reddit','user_id'=>(string)$author,'content_type'=>'text','text'=>$data['body']??$data['title']??$data['text']??null,'media_url'=>(string)$thing];
}
function reddit_send_reply(array $event,array $reply,string $token):void
{
    if(empty($event['media_url'])||$token==='')throw new InvalidArgumentException('Reddit thing ID and token are required');foreach(array_slice($reply['messages']??[],0,5)as$message){$ch=adapter_curl_init('https://oauth.reddit.com/api/comment');curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'User-Agent: mini-sns-bot/1.0','Content-Type: application/x-www-form-urlencoded'],CURLOPT_POSTFIELDS=>http_build_query(['api_type'=>'json','thing_id'=>$event['media_url'],'text'=>$message['text']??$message['media_url']??''])]);$result=curl_exec($ch);$status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE);$body=is_string($result)?json_decode($result,true):null;if($result===false||$status<200||$status>=300||!empty($body['json']['errors']))throw new RuntimeException('Reddit API request failed');curl_close($ch);}
}
