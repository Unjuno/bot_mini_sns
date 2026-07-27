import unittest

from platforms.telegram import TelegramAdapter


class TelegramAdapterTests(unittest.TestCase):
    def test_parse_supported_message_types(self):
        adapter = object.__new__(TelegramAdapter)
        cases = [
            ({"message": {"from": {"id": 1}, "chat": {"id": 2}, "text": "hi"}}, "text"),
            ({"message": {"from": {"id": 1}, "chat": {"id": 2}, "photo": [{"file_id": "small"}, {"file_id": "large"}]}}, "image"),
            ({"message": {"from": {"id": 1}, "chat": {"id": 2}, "audio": {"file_id": "a"}}}, "audio"),
            ({"message": {"from": {"id": 1}, "chat": {"id": 2}, "video": {"file_id": "v"}}}, "video"),
            ({"message": {"from": {"id": 1}, "chat": {"id": 2}, "document": {"file_id": "d"}}}, "file"),
        ]
        for payload, content_type in cases:
            with self.subTest(content_type=content_type):
                event = adapter.parse_event(payload)
                self.assertEqual(event.content_type, content_type)
                self.assertEqual(event.user_id, "1")
                self.assertEqual(event.reply_target, "2")

    def test_message_method_mapping(self):
        self.assertEqual(TelegramAdapter._message_request("image", "telegram:id", ""), ("sendPhoto", "photo", "id"))
        self.assertEqual(TelegramAdapter._message_request("file", "telegram:id", ""), ("sendDocument", "document", "id"))


if __name__ == "__main__":
    unittest.main()
