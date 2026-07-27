package main

import (
	"encoding/json"
	"net/http"
	"os"

	common "my_first_bot/go"
)

var posts []common.InboundEvent

func handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method != http.MethodPost { w.WriteHeader(http.StatusMethodNotAllowed); _ = json.NewEncoder(w).Encode(map[string]string{"error": "POST required"}); return }
	var event common.InboundEvent
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil { w.WriteHeader(http.StatusBadRequest); _ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"}); return }
	reply := common.ProcessEvent(event, &posts, 5)
	_ = json.NewEncoder(w).Encode(reply)
}

func main() {
	port := os.Getenv("PORT"); if port == "" { port = "8080" }
	http.HandleFunc("/webhook", handler)
	_ = http.ListenAndServe(":"+port, nil)
}
