import unittest

from core.models import InboundEvent
from core.service import MemoryPostRepository, process_event


class CoreServiceTests(unittest.TestCase):
    def test_reply_is_same_platform_and_same_type(self):
        repository = MemoryPostRepository()
        process_event(InboundEvent(platform="line", user_id="u1", content_type="text", text="one"), repository)
        process_event(InboundEvent(platform="telegram", user_id="u1", content_type="text", text="other"), repository)
        reply = process_event(InboundEvent(platform="line", user_id="u1", content_type="text", text="two"), repository)
        self.assertEqual([message.text for message in reply.messages], ["two", "one"])

    def test_reply_is_limited_by_adapter_capacity(self):
        repository = MemoryPostRepository()
        for number in range(7):
            process_event(InboundEvent(platform="line", user_id="u1", content_type="image", media_url=f"https://example/{number}"), repository, max_reply_items=5)
        reply = process_event(InboundEvent(platform="line", user_id="u1", content_type="image", media_url="https://example/latest"), repository, max_reply_items=5)
        self.assertEqual(len(reply.messages), 5)
        self.assertEqual(reply.messages[0].media_url, "https://example/latest")


if __name__ == "__main__":
    unittest.main()
