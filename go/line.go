package common

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

type LineAdapter struct { AccessToken string; Client *http.Client }

func (a LineAdapter) ParseEvent(payload map[string]any) (InboundEvent, error) {
	event := payload
	if events, ok := payload["events"].([]any); ok && len(events) > 0 { event, _ = events[0].(map[string]any) }
	message, _ := event["message"].(map[string]any)
	source, _ := event["source"].(map[string]any)
	userID, _ := source["userId"].(string); if userID == "" { return InboundEvent{}, fmt.Errorf("LINE event has no userId") }
	kind, _ := message["type"].(string); if kind == "" { kind = "text" }
	if kind == "document" { kind = "file" }
	text, _ := message["text"].(string); mediaID, _ := message["id"].(string); token, _ := event["replyToken"].(string)
	return InboundEvent{Platform:"line", UserID:userID, ContentType:kind, Text:text, MediaURL:mediaID, ReplyToken:token}, nil
}

func (a LineAdapter) SendReply(event InboundEvent, reply OutboundReply) error {
	if a.AccessToken == "" || event.ReplyToken == "" { return fmt.Errorf("LINE access token and reply token are required") }
	messages := make([]map[string]any, 0, 5)
	for _, message := range reply.Messages { payload := map[string]any{"type":"text", "text":message.Text}; if message.Type != "text" { if message.MediaURL == "" { return fmt.Errorf("LINE media reply requires media_url") }; payload = map[string]any{"type":message.Type, "originalContentUrl":message.MediaURL, "previewImageUrl":message.MediaURL}; if message.Type == "audio" { payload = map[string]any{"type":"audio", "originalContentUrl":message.MediaURL, "duration":1000} }; if message.Type == "file" { payload["fileName"] = message.Text }; }; messages = append(messages, payload); if len(messages) == 5 { break } }
	body, _ := json.Marshal(map[string]any{"replyToken":event.ReplyToken, "messages":messages}); request, _ := http.NewRequest(http.MethodPost, "https://api.line.me/v2/bot/message/reply", bytes.NewReader(body)); request.Header.Set("Authorization", "Bearer "+a.AccessToken); request.Header.Set("Content-Type", "application/json")
	client := a.Client; if client == nil { client = http.DefaultClient }; response, err := client.Do(request); if err != nil { return err }; defer response.Body.Close(); if response.StatusCode/100 != 2 { return fmt.Errorf("LINE API returned %s", response.Status) }; return nil
}
