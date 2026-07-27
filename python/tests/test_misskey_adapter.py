import unittest

from platforms.misskey import MisskeyAdapter


class MisskeyAdapterTests(unittest.TestCase):
    def test_parse_note_content(self):
        adapter = object.__new__(MisskeyAdapter)
        event = adapter.parse_event({"userId": "u1", "text": "hello", "files": []})
        self.assertEqual(event.platform, "misskey")
        self.assertEqual(event.content_type, "text")

    def test_media_type(self):
        self.assertEqual(MisskeyAdapter._content_type("image/png"), "image")
        self.assertEqual(MisskeyAdapter._content_type("application/pdf"), "file")


if __name__ == "__main__":
    unittest.main()
