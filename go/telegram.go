package common

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

type TelegramAdapter struct { Token string; Client *http.Client }

func (a TelegramAdapter) ParseEvent(payload map[string]any) (InboundEvent, error) {
	message, _ := payload["message"].(map[string]any); if message == nil { message, _ = payload["edited_message"].(map[string]any) }
	from, _ := message["from"].(map[string]any); chat, _ := message["chat"].(map[string]any); user, _ := from["id"].(float64); chatID, _ := chat["id"].(float64); if user == 0 || chatID == 0 { return InboundEvent{}, fmt.Errorf("Telegram update has no supported message") }
	event := InboundEvent{Platform:"telegram", UserID:fmt.Sprintf("%.0f", user), ReplyTarget:fmt.Sprintf("%.0f", chatID)}
	if text, ok := message["text"].(string); ok { event.ContentType="text"; event.Text=text; return event, nil }
	if photos, ok := message["photo"].([]any); ok && len(photos)>0 { last, _ := photos[len(photos)-1].(map[string]any); event.ContentType="image"; event.MediaURL="telegram:"+last["file_id"].(string); return event,nil }
	for _, item := range []struct{ key, kind string }{{"audio","audio"},{"video","video"},{"document","file"}} { if value, ok := message[item.key].(map[string]any); ok { event.ContentType=item.kind; event.MediaURL="telegram:"+value["file_id"].(string); return event,nil } }
	return InboundEvent{}, fmt.Errorf("Telegram content type is not supported")
}

func (a TelegramAdapter) SendReply(event InboundEvent, reply OutboundReply) error {
	for i, message := range reply.Messages { if i >= 10 { break }; method, field := "sendMessage", "text"; if message.Type != "text" { methods := map[string][2]string{"image":{"sendPhoto","photo"},"audio":{"sendAudio","audio"},"video":{"sendVideo","video"},"file":{"sendDocument","document"}}; pair, ok := methods[message.Type]; if !ok || message.MediaURL=="" { return fmt.Errorf("unsupported Telegram reply") }; method,field=pair[0],pair[1] }; value:=message.Text; if message.Type!="text" { value=strings.TrimPrefix(message.MediaURL, "telegram:") }; body:=map[string]any{"chat_id":event.ReplyTarget}; body[field]=value; if message.Type!="text"&&message.Text!="" { body["caption"]=message.Text }; data,_:=json.Marshal(body); req,_:=http.NewRequest(http.MethodPost,"https://api.telegram.org/bot"+a.Token+"/"+method,strings.NewReader(string(data))); req.Header.Set("Content-Type","application/json"); client:=a.Client;if client==nil{client=http.DefaultClient}; resp,err:=client.Do(req);if err!=nil{return err};resp.Body.Close();if resp.StatusCode/100!=2{return fmt.Errorf("Telegram API returned %s",resp.Status)} }
	return nil
}
