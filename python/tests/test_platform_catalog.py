import unittest

from platforms import PLATFORM_CATALOG


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


if __name__ == "__main__":
    unittest.main()
