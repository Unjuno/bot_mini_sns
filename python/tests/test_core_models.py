import unittest
from pydantic import ValidationError
from core.models import InboundEvent, OutboundMessage, OutboundReply


class TestInboundEvent(unittest.TestCase):
    def test_valid_text_event(self):
        event = InboundEvent(platform="line", user_id="U123", content_type="text", text="hello")
        self.assertEqual(event.platform, "line")
        self.assertEqual(event.text, "hello")

    def test_valid_media_event(self):
        event = InboundEvent(
            platform="telegram",
            user_id="TG456",
            content_type="image",
            media_url="https://example.com/photo.jpg",
        )
        self.assertEqual(event.content_type, "image")

    def test_missing_required_fields(self):
        with self.assertRaises(ValidationError):
            InboundEvent(platform="line")

    def test_invalid_content_type(self):
        with self.assertRaises(ValidationError):
            InboundEvent(platform="line", user_id="U1", content_type="sticker")

    def test_extra_fields_ignored(self):
        event = InboundEvent(
            platform="line", user_id="U1", content_type="text", text="hi", unknown_field="x"
        )
        self.assertFalse(hasattr(event, "unknown_field"))


class TestOutboundMessage(unittest.TestCase):
    def test_valid_message(self):
        msg = OutboundMessage(type="text", text="hello")
        self.assertEqual(msg.text, "hello")

    def test_invalid_type(self):
        with self.assertRaises(ValidationError):
            OutboundMessage(type="sticker", text="oops")


class TestOutboundReply(unittest.TestCase):
    def test_empty_messages(self):
        reply = OutboundReply(messages=[])
        self.assertEqual(reply.messages, [])

    def test_multiple_messages(self):
        reply = OutboundReply(
            messages=[
                OutboundMessage(type="text", text="first"),
                OutboundMessage(type="image", text="see image", media_url="https://example.com/img.jpg"),
            ]
        )
        self.assertEqual(len(reply.messages), 2)


if __name__ == "__main__":
    unittest.main()
