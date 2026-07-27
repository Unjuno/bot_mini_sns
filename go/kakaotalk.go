package common

import "fmt"

type KakaoTalkAdapter struct{}
func (KakaoTalkAdapter) ParseEvent(payload map[string]any)(InboundEvent,error){request,_:=payload["userRequest"].(map[string]any);userMap,_:=request["user"].(map[string]any);user:=fmt.Sprint(userMap["id"]);if user=="<nil>"||user==""{return InboundEvent{},fmt.Errorf("KakaoTalk request has no user")};return InboundEvent{Platform:"kakaotalk",UserID:user,ContentType:"text",Text:fmt.Sprint(request["utterance"])},nil}
func (KakaoTalkAdapter)RenderReply(reply OutboundReply)map[string]any{outputs:=[]map[string]any{};for i,message:=range reply.Messages{if i>=3{break};outputs=append(outputs,map[string]any{"simpleText":map[string]string{"text":message.Text}})};return map[string]any{"version":"2.0","template":map[string]any{"outputs":outputs}}}
