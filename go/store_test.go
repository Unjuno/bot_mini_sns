package common

import "testing"

func TestPostStorePersistsAndSharesContentAcrossPlatforms(t *testing.T) {
	store, err := OpenPostStore(t.TempDir() + "/posts.sqlite")
	if err != nil {
		t.Fatal(err)
	}
	defer store.Close()
	if _, err := store.ProcessEvent(InboundEvent{Platform: "line", UserID: "u1", ContentType: "text", Text: "line"}, 5); err != nil {
		t.Fatal(err)
	}
	reply, err := store.ProcessEvent(InboundEvent{Platform: "telegram", UserID: "u2", ContentType: "text", Text: "telegram"}, 5)
	if err != nil || len(reply.Messages) != 2 || reply.Messages[0].Text != "telegram" || reply.Messages[1].Text != "line" {
		t.Fatalf("unexpected reply: %#v, %v", reply, err)
	}
}
