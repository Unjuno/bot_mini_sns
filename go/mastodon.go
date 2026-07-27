package common

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
	"strings"
)

type MastodonAdapter struct {
	BaseURL, Token string
	Client         *http.Client
}

func (a MastodonAdapter) ParseEvent(payload map[string]any) (InboundEvent, error) {
	status := payload
	if nested, ok := payload["status"].(map[string]any); ok {
		status = nested
	}
	account, _ := status["account"].(map[string]any)
	user, _ := account["id"].(string)
	if user == "" {
		user, _ = status["user_id"].(string)
	}
	if user == "" {
		return InboundEvent{}, fmt.Errorf("Mastodon status has no account")
	}
	event := InboundEvent{Platform: "mastodon", UserID: user, ContentType: "text"}
	event.Text, _ = status["content"].(string)
	if id, ok := status["id"].(string); ok {
		event.ReplyToID = id
	}
	if media, ok := status["media_attachments"].([]any); ok && len(media) > 0 {
		item, _ := media[0].(map[string]any)
		event.MediaURL, _ = item["url"].(string)
		event.ContentType = fmt.Sprint(item["type"])
		if event.ContentType == "" {
			event.ContentType = "file"
		}
	}
	return event, nil
}

func (a MastodonAdapter) SendReply(event InboundEvent, reply OutboundReply) error {
	client := a.Client
	if client == nil {
		client = http.DefaultClient
	}
	for _, message := range reply.Messages {
		var mediaID string
		if message.Type != "text" {
			if message.MediaURL == "" {
				return fmt.Errorf("Mastodon %s reply requires media_url", message.Type)
			}
			mediaResp, err := client.Get(message.MediaURL)
			if err != nil {
				return err
			}
			if mediaResp.StatusCode/100 != 2 {
				mediaResp.Body.Close()
				return fmt.Errorf("Mastodon media download returned %s", mediaResp.Status)
			}
			data, err := io.ReadAll(mediaResp.Body)
			mediaResp.Body.Close()
			if err != nil {
				return err
			}
			var body bytes.Buffer
			writer := multipart.NewWriter(&body)
			header := make(textproto.MIMEHeader)
			header.Set("Content-Disposition", `form-data; name="file"; filename="reply.`+message.Type+`"`)
			header.Set("Content-Type", "application/octet-stream")
			part, err := writer.CreatePart(header)
			if err != nil {
				return err
			}
			if _, err = part.Write(data); err != nil {
				return err
			}
			if err = writer.Close(); err != nil {
				return err
			}
			req, _ := http.NewRequest(http.MethodPost, strings.TrimRight(a.BaseURL, "/")+"/api/v2/media", &body)
			req.Header.Set("Authorization", "Bearer "+a.Token)
			req.Header.Set("Content-Type", writer.FormDataContentType())
			resp, err := client.Do(req)
			if err != nil {
				return err
			}
			raw, readErr := io.ReadAll(resp.Body)
			resp.Body.Close()
			if readErr != nil {
				return readErr
			}
			if resp.StatusCode/100 != 2 {
				return fmt.Errorf("Mastodon media API returned %s", resp.Status)
			}
			var uploaded struct {
				ID string `json:"id"`
			}
			if err := json.Unmarshal(raw, &uploaded); err != nil || uploaded.ID == "" {
				return fmt.Errorf("Mastodon media upload returned no ID")
			}
			mediaID = uploaded.ID
		}
		post := map[string]any{"status": message.Text, "in_reply_to_id": event.ReplyToID}
		if mediaID != "" {
			post["media_ids"] = []string{mediaID}
		}
		data, _ := json.Marshal(post)
		req, _ := http.NewRequest(http.MethodPost, strings.TrimRight(a.BaseURL, "/")+"/api/v1/statuses", bytes.NewReader(data))
		req.Header.Set("Authorization", "Bearer "+a.Token)
		req.Header.Set("Content-Type", "application/json")
		resp, err := client.Do(req)
		if err != nil {
			return err
		}
		resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			return fmt.Errorf("Mastodon API returned %s", resp.Status)
		}
	}
	return nil
}
