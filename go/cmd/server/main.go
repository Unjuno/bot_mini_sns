package main

import (
	"encoding/json"
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
	var payload map[string]any
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"})
		return
	}
	event, adapter, err := runtimeEvent(payload)
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

func runtimeEvent(payload map[string]any) (common.InboundEvent, replyAdapter, error) {
	platform := os.Getenv("PLATFORM")
	switch platform {
	case "line":
		adapter := common.LineAdapter{AccessToken: os.Getenv("ACCESS_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, err
	case "telegram":
		adapter := common.TelegramAdapter{Token: os.Getenv("TELEGRAM_BOT_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, err
	case "discord":
		adapter := common.DiscordAdapter{Token: os.Getenv("DISCORD_BOT_TOKEN")}
		event, err := adapter.ParseEvent(payload)
		return event, adapter.SendReply, err
	default:
		var event common.InboundEvent
		data, err := json.Marshal(payload)
		if err != nil {
			return event, nil, err
		}
		if err := json.Unmarshal(data, &event); err != nil {
			return event, nil, err
		}
		return event, nil, nil
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
