package common

import (
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestImplementedAdaptersParseRepresentativeEvents(t *testing.T) {
	cases := []struct {
		name     string
		parse    func() (InboundEvent, error)
		platform string
	}{
		{"line", func() (InboundEvent, error) {
			return LineAdapter{}.ParseEvent(map[string]any{"events": []any{map[string]any{"source": map[string]any{"userId": "u"}, "message": map[string]any{"type": "text", "text": "x"}}}})
		}, "line"},
		{"telegram", func() (InboundEvent, error) {
			return TelegramAdapter{}.ParseEvent(map[string]any{"message": map[string]any{"from": map[string]any{"id": float64(1)}, "chat": map[string]any{"id": float64(2)}, "text": "x"}})
		}, "telegram"},
		{"discord", func() (InboundEvent, error) {
			return DiscordAdapter{}.ParseEvent(map[string]any{"d": map[string]any{"channel_id": "c", "author": map[string]any{"id": "u"}, "content": "x"}})
		}, "discord"},
		{"mastodon", func() (InboundEvent, error) {
			return MastodonAdapter{}.ParseEvent(map[string]any{"account": map[string]any{"id": "u"}, "id": "s", "content": "x"})
		}, "mastodon"},
		{"misskey", func() (InboundEvent, error) {
			return MisskeyAdapter{}.ParseEvent(map[string]any{"id": "n", "userId": "u", "text": "x"})
		}, "misskey"},
		{"bluesky", func() (InboundEvent, error) {
			return BlueskyAdapter{}.ParseEvent(map[string]any{"author": "did:u", "record": map[string]any{"text": "x"}})
		}, "bluesky"},
		{"slack", func() (InboundEvent, error) {
			return SlackAdapter{}.ParseEvent(map[string]any{"event": map[string]any{"user": "u", "channel": "c", "text": "x"}})
		}, "slack"},
		{"matrix", func() (InboundEvent, error) {
			return MatrixAdapter{}.ParseEvent(map[string]any{"event": map[string]any{"sender": "@u:test", "room_id": "!r:test", "content": map[string]any{"msgtype": "m.text", "body": "x"}}})
		}, "matrix"},
		{"whatsapp", func() (InboundEvent, error) {
			return WhatsAppAdapter{}.ParseEvent(map[string]any{"entry": []any{map[string]any{"changes": []any{map[string]any{"value": map[string]any{"messages": []any{map[string]any{"from": "u", "type": "text", "text": map[string]any{"body": "x"}}}}}}}}})
		}, "whatsapp"},
		{"viber", func() (InboundEvent, error) {
			return ViberAdapter{}.ParseEvent(map[string]any{"sender": map[string]any{"id": "u"}, "message": map[string]any{"type": "text", "text": "x"}})
		}, "viber"},
		{"zulip", func() (InboundEvent, error) {
			return ZulipAdapter{}.ParseEvent(map[string]any{"message": map[string]any{"sender_email": "u@test", "content": "x"}})
		}, "zulip"},
		{"google_chat", func() (InboundEvent, error) {
			return GoogleChatAdapter{}.ParseEvent(map[string]any{"space": map[string]any{"name": "spaces/1"}, "message": map[string]any{"sender": map[string]any{"name": "users/1"}, "text": "x"}})
		}, "google_chat"},
		{"teams", func() (InboundEvent, error) {
			return TeamsAdapter{}.ParseEvent(map[string]any{"from": map[string]any{"id": "u"}, "conversation": map[string]any{"id": "c"}, "text": "x"})
		}, "teams"},
		{"instagram", func() (InboundEvent, error) {
			return InstagramAdapter{}.ParseEvent(map[string]any{"entry": []any{map[string]any{"messaging": []any{map[string]any{"sender": map[string]any{"id": "u"}, "message": map[string]any{"text": "x"}}}}}})
		}, "instagram"},
		{"reddit", func() (InboundEvent, error) {
			return RedditAdapter{}.ParseEvent(map[string]any{"data": map[string]any{"author": map[string]any{"name": "u"}, "body": "x", "name": "t1_x"}})
		}, "reddit"},
		{"twitch", func() (InboundEvent, error) {
			return TwitchAdapter{}.ParseEvent(map[string]any{"event": map[string]any{"chatter_user_id": "u", "message_id": "m", "message": "x"}})
		}, "twitch"},
		{"kakaotalk", func() (InboundEvent, error) {
			return KakaoTalkAdapter{}.ParseEvent(map[string]any{"userRequest": map[string]any{"user": map[string]any{"id": "u"}, "utterance": "x"}})
		}, "kakaotalk"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			event, err := tc.parse()
			if err != nil {
				t.Fatal(err)
			}
			if event.Platform != tc.platform || event.ContentType != "text" {
				t.Fatalf("got %+v", event)
			}
		})
	}
}

func TestCommonCoreValidatesAndSharesSameTypeAcrossPlatforms(t *testing.T) {
	posts := []InboundEvent{{Platform: "line", UserID: "u", ContentType: "text", Text: "line"}}
	reply, err := ProcessEvent(InboundEvent{Platform: "telegram", UserID: "u2", ContentType: "text", Text: "telegram"}, &posts, 5)
	if err != nil || len(reply.Messages) != 2 || reply.Messages[0].Text != "telegram" || reply.Messages[1].Text != "line" { t.Fatalf("unexpected cross-platform reply: %#v, %v", reply, err) }
	if _, err := ProcessEvent(InboundEvent{Platform: "line", ContentType: "unknown"}, &posts, 5); err == nil { t.Fatal("invalid event accepted") }
}

type adapterRoundTripper struct{}

func (adapterRoundTripper) RoundTrip(*http.Request) (*http.Response, error) {
	return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(`{"ok":true,"result":"success","data":[{"is_sent":true}]}`)), Header: make(http.Header)}, nil
}

func TestImplementedAdaptersSendTextThroughHTTPMock(t *testing.T) {
	client := &http.Client{Transport: adapterRoundTripper{}}
	reply := OutboundReply{Messages: []OutboundMessage{{Type: "text", Text: "reply"}}}
	tests := []struct {
		name string
		send func() error
	}{
		{"line", func() error {
			return (LineAdapter{AccessToken: "token", Client: client}).SendReply(InboundEvent{ReplyToken: "r"}, reply)
		}},
		{"telegram", func() error {
			return (TelegramAdapter{Token: "token", Client: client}).SendReply(InboundEvent{ReplyTarget: "c"}, reply)
		}},
		{"discord", func() error {
			return (DiscordAdapter{Token: "token", Client: client}).SendReply(InboundEvent{ReplyTarget: "c"}, reply)
		}},
		{"mastodon", func() error {
			return (MastodonAdapter{BaseURL: "https://m.test", Token: "token", Client: client}).SendReply(InboundEvent{ReplyToID: "s"}, reply)
		}},
		{"misskey", func() error {
			return (MisskeyAdapter{BaseURL: "https://m.test", Token: "token", Client: client}).SendReply(InboundEvent{ReplyToID: "n"}, reply)
		}},
		{"bluesky", func() error {
			return (BlueskyAdapter{ServiceURL: "https://b.test", JWT: "jwt", Repo: "did:u", Client: client}).SendReply(InboundEvent{}, reply)
		}},
		{"slack", func() error {
			return (SlackAdapter{Token: "token", Client: client}).SendReply(InboundEvent{ReplyTarget: "c"}, reply)
		}},
		{"matrix", func() error {
			return (MatrixAdapter{BaseURL: "https://m.test", Token: "token", Client: client}).SendReply(InboundEvent{ReplyTarget: "!r:test"}, reply)
		}},
		{"whatsapp", func() error {
			return (WhatsAppAdapter{Token: "token", PhoneNumberID: "phone", Client: client}).SendReply(InboundEvent{UserID: "u"}, reply)
		}},
		{"viber", func() error {
			return (ViberAdapter{Token: "token", Client: client}).SendReply(InboundEvent{UserID: "u"}, reply)
		}},
		{"zulip", func() error {
			return (ZulipAdapter{BaseURL: "https://z.test", Email: "u", APIKey: "k", Client: client}).SendReply(InboundEvent{UserID: "u", ReplyMode: "direct"}, reply)
		}},
		{"google_chat", func() error {
			return (GoogleChatAdapter{Token: "token", Client: client}).SendReply(InboundEvent{ReplyTarget: "spaces/1"}, reply)
		}},
		{"teams", func() error {
			return (TeamsAdapter{Token: "token", ServiceURL: "https://t.test", Client: client}).SendReply(InboundEvent{ReplyTarget: "c"}, reply)
		}},
		{"instagram", func() error {
			return (InstagramAdapter{Token: "token", AccountID: "account", Client: client}).SendReply(InboundEvent{UserID: "u"}, reply)
		}},
		{"reddit", func() error {
			return (RedditAdapter{Token: "token", Client: client}).SendReply(InboundEvent{MediaURL: "t1_x"}, reply)
		}},
		{"twitch", func() error {
			return (TwitchAdapter{Token: "token", ClientID: "c", BroadcasterID: "b", SenderID: "s", Client: client}).SendReply(InboundEvent{}, reply)
		}},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if err := tc.send(); err != nil {
				t.Fatal(err)
			}
		})
	}
	if rendered := (KakaoTalkAdapter{}).RenderReply(reply); rendered["version"] != "2.0" {
		t.Fatalf("unexpected Kakao response: %#v", rendered)
	}
}
