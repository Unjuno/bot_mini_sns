package common

import "fmt"

var SupportedPlatforms = []string{
	"line", "telegram", "discord", "zulip", "matrix", "slack", "google_chat",
	"viber", "mastodon", "misskey", "bluesky", "whatsapp", "instagram", "teams",
	"kakaotalk", "twitch", "reddit",
}

func isSupportedPlatform(name string) bool {
	for _, platform := range SupportedPlatforms {
		if platform == name {
			return true
		}
	}
	return false
}

type InboundEvent struct {
	Platform    string `json:"platform"`
	UserID      string `json:"user_id"`
	ContentType string `json:"content_type"`
	Text        string `json:"text,omitempty"`
	MediaURL    string `json:"media_url,omitempty"`
	ReplyToken  string `json:"reply_token,omitempty"`
	ReplyTarget string `json:"reply_target,omitempty"`
	ReplyToID   string `json:"reply_to_id,omitempty"`
	ReplyToURI  string `json:"reply_to_uri,omitempty"`
	ReplyToCID  string `json:"reply_to_cid,omitempty"`
	ReplyMode   string `json:"reply_mode,omitempty"`
}

type OutboundMessage struct {
	Type     string `json:"type"`
	Text     string `json:"text"`
	MediaURL string `json:"media_url,omitempty"`
}

type OutboundReply struct {
	Messages []OutboundMessage `json:"messages"`
}

func ProcessEvent(event InboundEvent, posts *[]InboundEvent, limit int) (OutboundReply, error) {
	if !isSupportedPlatform(event.Platform) {
		return OutboundReply{}, fmt.Errorf("unsupported platform: %s", event.Platform)
	}
	if event.UserID == "" || event.ContentType == "" {
		return OutboundReply{}, fmt.Errorf("platform, user_id, and content_type are required")
	}
	if event.ContentType != "text" && event.ContentType != "image" && event.ContentType != "audio" && event.ContentType != "video" && event.ContentType != "file" {
		return OutboundReply{}, fmt.Errorf("unsupported content type: %s", event.ContentType)
	}
	if limit < 1 {
		return OutboundReply{}, fmt.Errorf("limit must be a positive integer")
	}
	*posts = append(*posts, event)
	result := OutboundReply{}
	for i := len(*posts) - 1; i >= 0 && len(result.Messages) < limit; i-- {
		post := (*posts)[i]
		if post.ContentType == event.ContentType {
			result.Messages = append(result.Messages, OutboundMessage{Type: post.ContentType, Text: post.Text, MediaURL: post.MediaURL})
		}
	}
	return result, nil
}
