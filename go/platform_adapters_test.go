package common

import "testing"

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
