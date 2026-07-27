import unittest

from platforms.bluesky import BlueskyAdapter
from platforms.mastodon import MastodonAdapter


class SocialAdapterTests(unittest.TestCase):
    def test_mastodon_status_parser(self):
        adapter = object.__new__(MastodonAdapter)
        event = adapter.parse_event({"account": {"id": "u"}, "text": "hello"})
        self.assertEqual(event.content_type, "text")

    def test_bluesky_record_parser(self):
        adapter = object.__new__(BlueskyAdapter)
        event = adapter.parse_event({"did": "did:plc:test", "record": {"text": "hello"}})
        self.assertEqual(event.platform, "bluesky")


if __name__ == "__main__":
    unittest.main()
