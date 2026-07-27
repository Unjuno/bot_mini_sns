import unittest

from platforms import MockPlatformAdapter, PLATFORM_CATALOG


class PlatformCatalogTests(unittest.TestCase):
    def test_all_documented_platforms_are_declared(self):
        expected = {
            "line", "telegram", "discord", "zulip", "matrix", "slack",
            "google_chat", "viber", "mastodon", "misskey", "bluesky",
            "whatsapp", "instagram", "teams", "kakaotalk", "twitch", "reddit",
        }
        self.assertEqual(set(PLATFORM_CATALOG), expected)

    def test_every_platform_has_common_content_contract(self):
        for capabilities in PLATFORM_CATALOG.values():
            with self.subTest(platform=capabilities.name):
                self.assertEqual(capabilities.receive_types, capabilities.send_types)
                self.assertGreater(capabilities.max_reply_items or 0, 0)

    def test_every_platform_can_validate_and_send_a_common_event_offline(self):
        for name in PLATFORM_CATALOG:
            with self.subTest(platform=name):
                adapter = MockPlatformAdapter(name)
                event = adapter.parse_event({
                    "platform": name,
                    "user_id": "test-user",
                    "content_type": "text",
                    "text": "hello",
                })
                adapter.send_reply(event, type("Reply", (), {"messages": []})())
                self.assertEqual(len(adapter.sent_replies), 1)


if __name__ == "__main__":
    unittest.main()
