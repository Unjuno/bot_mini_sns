import unittest

from platforms.discord import DiscordAdapter


class DiscordAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = object.__new__(DiscordAdapter)

    def test_parse_text_and_attachment(self):
        text = self.adapter.parse_event({"t": "MESSAGE_CREATE", "d": {"channel_id": "c", "author": {"id": "u"}, "content": "hello"}})
        image = self.adapter.parse_event({"t": "MESSAGE_CREATE", "d": {"channel_id": "c", "author": {"id": "u"}, "attachments": [{"content_type": "image/png", "url": "https://cdn/image.png"}]}})
        self.assertEqual(text.content_type, "text")
        self.assertEqual(image.content_type, "image")

    def test_content_type_fallbacks(self):
        self.assertEqual(self.adapter._content_type("video/mp4", "x.mp4"), "video")
        self.assertEqual(self.adapter._content_type("application/pdf", "x.pdf"), "file")


if __name__ == "__main__":
    unittest.main()
