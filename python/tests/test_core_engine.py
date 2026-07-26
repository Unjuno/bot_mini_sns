import unittest
from core.engine import (
    Action,
    ActionType,
    build_reply,
    decide_actions,
    format_recent_posts_text,
    format_usage_text,
)
from core.models import InboundEvent


class TestDecideActions(unittest.TestCase):
    def test_first_text_post_triggers_save_and_usage(self):
        event = InboundEvent(platform="line", user_id="U1", content_type="text", text="hello")
        actions = decide_actions(is_first_post=True, event=event)
        types = [a.type for a in actions]
        self.assertIn(ActionType.SAVE_TEXT, types)
        self.assertIn(ActionType.SHOW_USAGE, types)
        self.assertNotIn(ActionType.REPLY_RECENT_POSTS, types)

    def test_first_image_post_triggers_save_media_and_usage(self):
        event = InboundEvent(
            platform="line", user_id="U1", content_type="image", media_url="https://example.com/img.jpg"
        )
        actions = decide_actions(is_first_post=True, event=event)
        types = [a.type for a in actions]
        self.assertIn(ActionType.SAVE_MEDIA, types)
        self.assertIn(ActionType.SHOW_USAGE, types)
        self.assertNotIn(ActionType.REPLY_RECENT_POSTS, types)

    def test_second_text_post_triggers_save_and_recent(self):
        event = InboundEvent(platform="line", user_id="U1", content_type="text", text="second post")
        actions = decide_actions(is_first_post=False, event=event)
        types = [a.type for a in actions]
        self.assertIn(ActionType.SAVE_TEXT, types)
        self.assertIn(ActionType.REPLY_RECENT_POSTS, types)
        self.assertNotIn(ActionType.SHOW_USAGE, types)

    def test_second_image_post_triggers_save_media_and_recent(self):
        event = InboundEvent(
            platform="telegram", user_id="TG1", content_type="image", media_url="https://example.com/img2.jpg"
        )
        actions = decide_actions(is_first_post=False, event=event)
        types = [a.type for a in actions]
        self.assertIn(ActionType.SAVE_MEDIA, types)
        self.assertIn(ActionType.REPLY_RECENT_POSTS, types)

    def test_audio_and_video_and_file_also_save_media(self):
        for ct in ("audio", "video", "file"):
            with self.subTest(content_type=ct):
                event = InboundEvent(platform="line", user_id="U1", content_type=ct)
                actions = decide_actions(is_first_post=False, event=event)
                types = [a.type for a in actions]
                self.assertIn(ActionType.SAVE_MEDIA, types)

    def test_no_keyword_branching(self):
        event = InboundEvent(platform="line", user_id="U1", content_type="text", text="任意の文章")
        actions = decide_actions(is_first_post=False, event=event)
        types = [a.type for a in actions]
        self.assertNotIn(ActionType.SHOW_USAGE, types)

    def test_no_push_action_type_exists(self):
        all_types = set(ActionType)
        push_like = {"SHOW_USAGE", "SAVE_TEXT", "SAVE_MEDIA", "REPLY_RECENT_POSTS"}
        self.assertEqual(all_types, {ActionType[t] for t in push_like})


class TestFormatUsageText(unittest.TestCase):
    def test_contains_keywords(self):
        text = format_usage_text()
        self.assertIn("使い方", text)
        self.assertIn("文章", text)
        self.assertIn("写真", text)


class TestFormatRecentPosts(unittest.TestCase):
    def test_empty_posts(self):
        result = format_recent_posts_text([])
        self.assertIn("保存済みの投稿", result)
        self.assertNotIn("・", result)

    def test_single_text_post(self):
        posts = [{"type": "text", "text": "hello world"}]
        result = format_recent_posts_text(posts)
        self.assertIn("hello world", result)
        self.assertIn("文章", result)

    def test_media_post_without_text(self):
        posts = [{"type": "image", "text": None}]
        result = format_recent_posts_text(posts)
        self.assertIn("写真", result)

    def test_long_text_is_truncated(self):
        long = "a" * 200
        posts = [{"type": "text", "text": long}]
        result = format_recent_posts_text(posts)
        self.assertNotIn(long, result)

    def test_multiple_posts_in_order(self):
        posts = [
            {"type": "text", "text": "first"},
            {"type": "image", "text": None},
            {"type": "audio", "text": "音声メモ"},
        ]
        result = format_recent_posts_text(posts)
        self.assertIn("first", result)
        self.assertIn("写真", result)
        self.assertIn("音声メモ", result)

    def test_newlines_are_replaced(self):
        posts = [{"type": "text", "text": "line1\nline2\nline3"}]
        result = format_recent_posts_text(posts)
        self.assertIn("line1 line2 line3", result)
        self.assertNotIn("line1\nline2", result)


class TestBuildReply(unittest.TestCase):
    def test_usage_reply_has_no_post_list(self):
        actions = [Action(ActionType.SAVE_TEXT, text="hi"), Action(ActionType.SHOW_USAGE)]
        reply = build_reply(actions)
        self.assertEqual(len(reply.messages), 1)
        self.assertIn("使い方", reply.messages[0].text)

    def test_recent_reply_includes_posts(self):
        actions = [Action(ActionType.SAVE_TEXT, text="hi"), Action(ActionType.REPLY_RECENT_POSTS)]
        recent = [{"type": "text", "text": "previous post"}]
        reply = build_reply(actions, recent_posts=recent)
        self.assertEqual(len(reply.messages), 1)
        self.assertIn("previous post", reply.messages[0].text)

    def test_recent_reply_with_no_posts(self):
        actions = [Action(ActionType.SAVE_TEXT, text="hi"), Action(ActionType.REPLY_RECENT_POSTS)]
        reply = build_reply(actions, recent_posts=[])
        self.assertIn("投稿しました", reply.messages[0].text)

    def test_action_list_empty(self):
        reply = build_reply([])
        self.assertEqual(reply.messages, [])


if __name__ == "__main__":
    unittest.main()
