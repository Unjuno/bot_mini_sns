import unittest

from core.models import OutboundMessage, OutboundReply
from platforms.matrix import MatrixAdapter
from platforms.slack import SlackAdapter
from platforms.zulip import ZulipAdapter
from platforms.google_chat import GoogleChatAdapter
from platforms.viber import ViberAdapter
from platforms.whatsapp import WhatsAppAdapter
from platforms.instagram import InstagramAdapter
from platforms.teams import TeamsAdapter
from platforms.twitch import TwitchAdapter
from platforms.reddit import RedditAdapter
from platforms.line import LineAdapter


class Response:
    def raise_for_status(self): pass
    def json(self): return {"ok": True}


class Session:
    def __init__(self): self.calls = []
    def post(self, *args, **kwargs): self.calls.append(("post", args, kwargs)); return Response()
    def put(self, *args, **kwargs): self.calls.append(("put", args, kwargs)); return Response()


class NativeTextAdapterTests(unittest.TestCase):
    def test_zulip_event_and_reply(self):
        session = Session(); adapter = ZulipAdapter("https://zulip.test", "bot@test", "key", session)
        event = adapter.parse_event({"message": {"sender_email": "u@test", "content": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "u@test"); self.assertEqual(session.calls[0][0], "post")
        stream_event = adapter.parse_event({"message": {"type": "stream", "sender_email": "u@test", "display_recipient": "general", "subject": "topic", "content": "hello"}})
        adapter.send_reply(stream_event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(session.calls[1][2]["data"]["type"], "stream")

    def test_matrix_event_and_reply(self):
        session = Session(); adapter = MatrixAdapter("https://matrix.test", "token", session)
        event = adapter.parse_event({"event": {"sender": "@u:test", "room_id": "!room:test", "content": {"msgtype": "m.text", "body": "hello"}}})
        import os
        old = os.environ.get("MATRIX_ROOM_ID"); os.environ["MATRIX_ROOM_ID"] = "!room:test"
        try: adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        finally:
            if old is None: os.environ.pop("MATRIX_ROOM_ID", None)
            else: os.environ["MATRIX_ROOM_ID"] = old
        self.assertEqual(session.calls[0][0], "put")

    def test_slack_event_and_reply(self):
        session = Session(); adapter = SlackAdapter("xoxb-token", session)
        event = adapter.parse_event({"event": {"user": "U1", "channel": "C1", "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "U1"); self.assertEqual(session.calls[0][2]["json"]["channel"], "C1")

    def test_google_chat_event_and_reply(self):
        session = Session(); adapter = GoogleChatAdapter("token", session)
        event = adapter.parse_event({"space": {"name": "spaces/1"}, "message": {"sender": {"name": "users/1"}, "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "users/1"); self.assertEqual(event.reply_target, "spaces/1"); self.assertEqual(session.calls[0][0], "post")

    def test_viber_event_and_reply(self):
        session = Session(); adapter = ViberAdapter("token", session)
        event = adapter.parse_event({"sender": {"id": "u"}, "message": {"type": "text", "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "u")

    def test_meta_adapters_parse_events(self):
        whatsapp = WhatsAppAdapter("token", "phone", Session())
        event = whatsapp.parse_event({"entry": [{"changes": [{"value": {"messages": [{"from": "u", "type": "text", "text": {"body": "hello"}}]}}]}]})
        self.assertEqual(event.user_id, "u")
        file_event = whatsapp.parse_event({"entry": [{"changes": [{"value": {"messages": [{"from": "u", "type": "document", "document": {"id": "m1"}}]}}]}]})
        self.assertEqual(file_event.content_type, "file"); self.assertEqual(file_event.media_url, "m1")
        instagram = InstagramAdapter("token", "account", Session())
        self.assertEqual(instagram.parse_event({"entry": [{"messaging": [{"sender": {"id": "ig"}, "message": {"text": "hello"}}]}]}).user_id, "ig")

    def test_teams_event_and_reply(self):
        import os
        session = Session(); adapter = TeamsAdapter("token", session)
        event = adapter.parse_event({"from": {"id": "u"}, "conversation": {"id": "c"}, "text": "hello"})
        old = os.environ.get("TEAMS_SERVICE_URL"); os.environ["TEAMS_SERVICE_URL"] = "https://teams.test"
        try: adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        finally:
            if old is None: os.environ.pop("TEAMS_SERVICE_URL", None)
            else: os.environ["TEAMS_SERVICE_URL"] = old
        self.assertEqual(session.calls[0][0], "post"); self.assertEqual(event.reply_target, "c")

    def test_twitch_and_reddit_events(self):
        twitch = TwitchAdapter("token", "client", "broadcaster", "sender", Session())
        twitch_event = twitch.parse_event({"event": {"chatter_user_id": "u", "message_id": "m1", "message": "hello"}})
        self.assertEqual(twitch_event.user_id, "u"); self.assertEqual(twitch_event.reply_to_id, "m1")
        reddit = RedditAdapter("token", Session())
        self.assertEqual(reddit.parse_event({"data": {"author": {"name": "u"}, "body": "hello", "name": "t1_x"}}).media_url, "t1_x")

    def test_line_event_and_reply(self):
        session = Session(); adapter = LineAdapter("token", session)
        event = adapter.parse_event({"events": [{"replyToken": "rt", "source": {"userId": "u"}, "message": {"type": "text", "text": "hello"}}]})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "u"); self.assertEqual(session.calls[0][1][0], "https://api.line.me/v2/bot/message/reply")
        self.assertEqual(session.calls[0][2]["json"]["replyToken"], "rt")

    def test_line_media_reply_uses_native_message_types(self):
        session = Session(); adapter = LineAdapter("token", session)
        event = adapter.parse_event({"events": [{"replyToken": "rt", "source": {"userId": "u"}, "message": {"type": "image", "id": "m1"}}]})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="image", media_url="https://cdn.test/image.jpg")]))
        self.assertEqual(session.calls[0][2]["json"]["messages"][0]["type"], "image")
        self.assertEqual(session.calls[0][2]["json"]["messages"][0]["originalContentUrl"], "https://cdn.test/image.jpg")


if __name__ == "__main__": unittest.main()
