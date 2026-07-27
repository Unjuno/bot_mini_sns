package common

type InboundEvent struct {
	Platform    string `json:"platform"`
	UserID      string `json:"user_id"`
	ContentType string `json:"content_type"`
	Text        string `json:"text,omitempty"`
	MediaURL    string `json:"media_url,omitempty"`
}

type OutboundMessage struct {
	Type     string `json:"type"`
	Text     string `json:"text"`
	MediaURL string `json:"media_url,omitempty"`
}

type OutboundReply struct {
	Messages []OutboundMessage `json:"messages"`
}

func ProcessEvent(event InboundEvent, posts *[]InboundEvent, limit int) OutboundReply {
	*posts = append(*posts, event)
	result := OutboundReply{}
	for i := len(*posts) - 1; i >= 0 && len(result.Messages) < limit; i-- {
		post := (*posts)[i]
		if post.Platform == event.Platform && post.UserID == event.UserID && post.ContentType == event.ContentType {
			result.Messages = append(result.Messages, OutboundMessage{Type: post.ContentType, Text: post.Text, MediaURL: post.MediaURL})
		}
	}
	return result
}
