<?php

declare(strict_types=1);

/** @return array<string,mixed> */
function kakaotalk_parse_event(array $payload): array
{
    $request=$payload['userRequest']??[];$user=$request['user']['id']??$payload['user_id']??'';if($user==='')throw new InvalidArgumentException('KakaoTalk request has no user');return ['platform'=>'kakaotalk','user_id'=>(string)$user,'content_type'=>'text','text'=>$request['utterance']??''];
}
/** @return array<string,mixed> */
function kakaotalk_render_reply(array $reply): array
{
    $outputs=[];foreach(array_slice($reply['messages']??[],0,3)as$message)$outputs[]=['simpleText'=>['text'=>$message['text']??$message['media_url']??'']];return ['version'=>'2.0','template'=>['outputs'=>$outputs]];
}
