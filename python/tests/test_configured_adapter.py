import unittest

from platforms.configured import ConfiguredHTTPAdapter


class ConfiguredAdapterTests(unittest.TestCase):
    def test_normalized_event_round_trip(self):
        adapter = ConfiguredHTTPAdapter("slack", endpoint="https://example.test/events")
        event = adapter.parse_event({"event": {"platform": "slack", "user_id": "u", "content_type": "text", "text": "hi"}})
        self.assertEqual(event.text, "hi")
        self.assertEqual(adapter.capabilities.name, "slack")


if __name__ == "__main__":
    unittest.main()
