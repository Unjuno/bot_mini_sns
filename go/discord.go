package common

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type DiscordAdapter struct { Token string; Client *http.Client }

func (a DiscordAdapter) ParseEvent(payload map[string]any) (InboundEvent, error) {
	message := payload; if nested, ok := payload["d"].(map[string]any); ok { message = nested }
	author, _ := message["author"].(map[string]any); user, _ := author["id"].(string); channel, _ := message["channel_id"].(string); if user==""||channel=="" { return InboundEvent{}, fmt.Errorf("Discord message has no channel or author") }
	event:=InboundEvent{Platform:"discord",UserID:user,ReplyTarget:channel}; if text,ok:=message["content"].(string);ok&&text!="" {event.ContentType="text";event.Text=text;return event,nil}; attachments,_:=message["attachments"].([]any);if len(attachments)==0{return InboundEvent{},fmt.Errorf("Discord message has no supported content")}; attachment,_:=attachments[0].(map[string]any);url,_:=attachment["url"].(string);if url==""{return InboundEvent{},fmt.Errorf("Discord attachment has no URL")};mime,_:=attachment["content_type"].(string);event.ContentType=discordContentType(mime,fmt.Sprint(attachment["filename"]));event.MediaURL=url;return event,nil
}
func discordContentType(mime, filename string) string { value:=strings.ToLower(mime+" "+filename);if strings.HasPrefix(value,"image/")||strings.Contains(value,".png")||strings.Contains(value,".jpg"){return "image"};if strings.HasPrefix(value,"audio/"){return "audio"};if strings.HasPrefix(value,"video/"){return "video"};return "file" }
func (a DiscordAdapter) SendReply(event InboundEvent, reply OutboundReply) error { if event.ReplyTarget==""{return fmt.Errorf("Discord reply_target is required")};client:=a.Client;if client==nil{client=http.DefaultClient};for i,message:=range reply.Messages{if i>=10{break};body,_:=json.Marshal(map[string]any{"content":message.Text,"allowed_mentions":map[string]any{"parse":[]string{}}});req,_:=http.NewRequest(http.MethodPost,"https://discord.com/api/v10/channels/"+event.ReplyTarget+"/messages",bytes.NewReader(body));req.Header.Set("Authorization","Bot "+a.Token);req.Header.Set("Content-Type","application/json");resp,err:=client.Do(req);if err!=nil{return err};io.Copy(io.Discard,resp.Body);resp.Body.Close();if resp.StatusCode/100!=2{return fmt.Errorf("Discord API returned %s",resp.Status)}};return nil }
