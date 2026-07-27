import unittest

from platforms.configured import ConfiguredHTTPAdapter
from platforms.catalog import PLATFORM_CATALOG
from core.models import InboundEvent, OutboundMessage, OutboundReply


class FakeResponse:
    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse()


class ConfiguredAdapterTests(unittest.TestCase):
    def test_normalized_event_round_trip(self):
        adapter = ConfiguredHTTPAdapter("slack", endpoint="https://example.test/events")
        event = adapter.parse_event({"event": {"platform": "slack", "user_id": "u", "content_type": "text", "text": "hi"}})
        self.assertEqual(event.text, "hi")
        self.assertEqual(adapter.capabilities.name, "slack")

    def test_every_configured_platform_can_parse_and_send_without_credentials(self):
        configured = {"zulip", "matrix", "slack", "google_chat", "viber", "whatsapp",
                      "instagram", "teams", "kakaotalk", "twitch", "reddit"}
        for platform in configured:
            with self.subTest(platform=platform):
                session = FakeSession()
                adapter = ConfiguredHTTPAdapter(platform, endpoint="https://example.test/send", session=session)
                event = adapter.parse_event({"platform": platform, "user_id": "u", "content_type": "text", "text": "hi"})
                adapter.send_reply(event, OutboundReply(messages=[OutboundMessage(type="text", text="reply")]))
                self.assertEqual(len(session.calls), 1)
                self.assertEqual(session.calls[0][0][0], "https://example.test/send")
                self.assertEqual(session.calls[0][1]["json"]["reply"]["messages"][0]["text"], "reply")


if __name__ == "__main__":
    unittest.main()
