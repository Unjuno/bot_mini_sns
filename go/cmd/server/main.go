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
	var event common.InboundEvent
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"})
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
	_ = json.NewEncoder(w).Encode(reply)
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
