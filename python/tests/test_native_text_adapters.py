import unittest

from core.models import OutboundMessage, OutboundReply
from platforms.matrix import MatrixAdapter
from platforms.slack import SlackAdapter
from platforms.zulip import ZulipAdapter


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


if __name__ == "__main__": unittest.main()
