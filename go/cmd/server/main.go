package main

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"sync"

	common "my_first_bot/go"
)

var posts []common.InboundEvent
var postsPath = "posts.json"
var postsMu sync.Mutex

func loadPosts() {
	data, err := os.ReadFile(postsPath)
	if err == nil {
		_ = json.Unmarshal(data, &posts)
	}
}

func savePosts() {
	data, _ := json.MarshalIndent(posts, "", "  ")
	_ = os.WriteFile(postsPath, data, 0600)
}

func handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "POST required"})
		return
	}
	rawBody, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid body"})
		return
	}
	if os.Getenv("PLATFORM") == "line" && !common.VerifyHMACSHA256(rawBody, os.Getenv("CHANNEL_SECRET"), r.Header.Get("X-Line-Signature"), "") {
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid LINE signature"})
		return
	}
	var payload map[string]any
	if err := json.Unmarshal(rawBody, &payload); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"})
		return
	}
	event, adapter, renderReply, err := runtimeEvent(payload)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}
	postsMu.Lock()
	defer postsMu.Unlock()
	reply, err := common.ProcessEvent(event, &posts, 5)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}
	savePosts()
	if renderReply != nil {
		if err := renderReply(w, reply); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
			return
		}
		return
	}
	if adapter != nil {
		if err := adapter(event, reply); err != nil {
			w.WriteHeader(http.StatusBadGateway)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
			return
		}
	}
	_ = json.NewEncoder(w).Encode(reply)
}

type replyAdapter func(common.InboundEvent, common.OutboundReply) error
type replyRenderer func(http.ResponseWriter, common.OutboundReply) error

func runtimeEvent(payload map[string]any) (common.InboundEvent, replyAdapter, replyRenderer, error) {
	platform := os.Getenv("PLATFORM")
	switch platform {
	case "line":
		adapter := common.LineAdapter{AccessToken: os.Getenv("ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "telegram":
		adapter := common.TelegramAdapter{Token: os.Getenv("TELEGRAM_BOT_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "discord":
		adapter := common.DiscordAdapter{Token: os.Getenv("DISCORD_BOT_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "mastodon":
		adapter := common.MastodonAdapter{BaseURL: os.Getenv("MASTODON_BASE_URL"), Token: os.Getenv("MASTODON_ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "misskey":
		adapter := common.MisskeyAdapter{BaseURL: os.Getenv("MISSKEY_BASE_URL"), Token: os.Getenv("MISSKEY_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "bluesky":
		adapter := common.BlueskyAdapter{ServiceURL: os.Getenv("BLUESKY_SERVICE_URL"), JWT: os.Getenv("BLUESKY_ACCESS_JWT"), Repo: os.Getenv("BLUESKY_REPO")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "slack":
		adapter := common.SlackAdapter{Token: os.Getenv("SLACK_BOT_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "matrix":
		adapter := common.MatrixAdapter{BaseURL: os.Getenv("MATRIX_BASE_URL"), Token: os.Getenv("MATRIX_ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "whatsapp":
		adapter := common.WhatsAppAdapter{Token: os.Getenv("WHATSAPP_ACCESS_TOKEN"), PhoneNumberID: os.Getenv("WHATSAPP_PHONE_NUMBER_ID")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "viber":
		adapter := common.ViberAdapter{Token: os.Getenv("VIBER_AUTH_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "zulip":
		adapter := common.ZulipAdapter{BaseURL: os.Getenv("ZULIP_BASE_URL"), Email: os.Getenv("ZULIP_EMAIL"), APIKey: os.Getenv("ZULIP_API_KEY")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "google_chat":
		adapter := common.GoogleChatAdapter{Token: os.Getenv("GOOGLE_CHAT_ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "teams":
		adapter := common.TeamsAdapter{Token: os.Getenv("TEAMS_BOT_TOKEN"), ServiceURL: os.Getenv("TEAMS_SERVICE_URL")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "instagram":
		adapter := common.InstagramAdapter{Token: os.Getenv("INSTAGRAM_ACCESS_TOKEN"), AccountID: os.Getenv("INSTAGRAM_ACCOUNT_ID")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "reddit":
		adapter := common.RedditAdapter{Token: os.Getenv("REDDIT_ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "twitch":
		adapter := common.TwitchAdapter{Token: os.Getenv("TWITCH_ACCESS_TOKEN"), ClientID: os.Getenv("TWITCH_CLIENT_ID"), BroadcasterID: os.Getenv("TWITCH_BROADCASTER_ID"), SenderID: os.Getenv("TWITCH_SENDER_ID")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, nil, err
	case "kakaotalk":
		adapter := common.KakaoTalkAdapter{}
		event, err := adapter.ParseEvent(payload)
		return event, nil, func(w http.ResponseWriter, reply common.OutboundReply) error {
			return json.NewEncoder(w).Encode(adapter.RenderReply(reply))
		}, err
	default:
		var event common.InboundEvent
		data, err := json.Marshal(payload)
		if err != nil {
			return event, nil, nil, err
		}
		if err := json.Unmarshal(data, &event); err != nil {
			return event, nil, nil, err
		}
		return event, nil, nil, nil
	}
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	if configured := os.Getenv("POSTS_FILE"); configured != "" {
		postsPath = configured
	}
	loadPosts()
	http.HandleFunc("/webhook", handler)
	_ = http.ListenAndServe(":"+port, nil)
}
