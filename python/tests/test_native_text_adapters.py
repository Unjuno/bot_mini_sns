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
from platforms.kakaotalk import KakaoTalkAdapter


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

    def test_matrix_event_and_reply(self):
        session = Session(); adapter = MatrixAdapter("https://matrix.test", "token", session)
        event = adapter.parse_event({"event": {"sender": "@u:test", "content": {"msgtype": "m.text", "body": "hello"}}})
        import os
        old = os.environ.get("MATRIX_ROOM_ID"); os.environ["MATRIX_ROOM_ID"] = "!room:test"
        try: adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        finally:
            if old is None: os.environ.pop("MATRIX_ROOM_ID", None)
            else: os.environ["MATRIX_ROOM_ID"] = old
        self.assertEqual(session.calls[0][0], "put")

    def test_slack_event_and_reply(self):
        session = Session(); adapter = SlackAdapter("xoxb-token", session)
        event = adapter.parse_event({"event": {"user": "U1", "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "U1"); self.assertEqual(session.calls[0][2]["json"]["channel"], "U1")

    def test_google_chat_event_and_reply(self):
        session = Session(); adapter = GoogleChatAdapter("token", session)
        event = adapter.parse_event({"message": {"sender": {"name": "users/1"}, "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "users/1"); self.assertEqual(session.calls[0][0], "post")

    def test_viber_event_and_reply(self):
        session = Session(); adapter = ViberAdapter("token", session)
        event = adapter.parse_event({"sender": {"id": "u"}, "message": {"type": "text", "text": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "u")

    def test_meta_adapters_parse_events(self):
        whatsapp = WhatsAppAdapter("token", "phone", Session())
        event = whatsapp.parse_event({"entry": [{"changes": [{"value": {"messages": [{"from": "u", "type": "text", "text": {"body": "hello"}}]}}]}]})
        self.assertEqual(event.user_id, "u")
        instagram = InstagramAdapter("token", "account", Session())
        self.assertEqual(instagram.parse_event({"sender": {"id": "ig"}, "message": {"text": "hello"}}).user_id, "ig")

    def test_teams_event_and_reply(self):
        import os
        session = Session(); adapter = TeamsAdapter("token", session)
        event = adapter.parse_event({"from": {"id": "u"}, "conversation": {"id": "c"}, "text": "hello"})
        old = os.environ.get("TEAMS_SERVICE_URL"); os.environ["TEAMS_SERVICE_URL"] = "https://teams.test"
        try: adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        finally:
            if old is None: os.environ.pop("TEAMS_SERVICE_URL", None)
            else: os.environ["TEAMS_SERVICE_URL"] = old
        self.assertEqual(session.calls[0][0], "post")

    def test_twitch_and_reddit_events(self):
        twitch = TwitchAdapter("token", "client", "broadcaster", "sender", Session())
        self.assertEqual(twitch.parse_event({"event": {"chatter_user_id": "u", "message": "hello"}}).user_id, "u")
        reddit = RedditAdapter("token", Session())
        self.assertEqual(reddit.parse_event({"data": {"author": {"name": "u"}, "body": "hello", "name": "t1_x"}}).media_url, "t1_x")

    def test_kakao_event_and_reply(self):
        session = Session(); adapter = KakaoTalkAdapter("https://kakao.test", session)
        event = adapter.parse_event({"userRequest": {"user": {"id": "u"}, "utterance": "hello"}})
        adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
        self.assertEqual(event.user_id, "u")


if __name__ == "__main__": unittest.main()
