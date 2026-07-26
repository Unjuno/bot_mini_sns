import os
import tempfile
import unittest
from pathlib import Path

from core.database import (
    create_user,
    ensure_user,
    get_recent_posts,
    get_user,
    has_posts,
    init_db,
    save_post,
)


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test.db"
        init_db(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        from core.database import db_connection

        with db_connection(self.db_path) as db:
            db.execute("DELETE FROM post_reads")
            db.execute("DELETE FROM posts")
            db.execute("DELETE FROM users")

    def test_init_db_creates_tables(self):
        from core.database import db_connection

        with db_connection(self.db_path) as db:
            tables = {row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("users", tables)
        self.assertIn("posts", tables)

    def test_get_user_returns_none_for_missing(self):
        user = get_user(self.db_path, "U-nonexistent")
        self.assertIsNone(user)

    def test_create_and_get_user(self):
        user = create_user(self.db_path, "U-test", "Test User")
        self.assertIsNotNone(user)
        self.assertEqual(user["display_name"], "Test User")
        fetched = get_user(self.db_path, "U-test")
        self.assertEqual(fetched["id"], user["id"])

    def test_ensure_user_creates_if_missing(self):
        user = ensure_user(self.db_path, "U-new")
        self.assertIsNotNone(user)
        self.assertEqual(user["line_user_id"], "U-new")

    def test_ensure_user_returns_existing(self):
        u1 = ensure_user(self.db_path, "U-existing")
        u2 = ensure_user(self.db_path, "U-existing")
        self.assertEqual(u1["id"], u2["id"])

    def test_has_posts_false_for_new_user(self):
        user = create_user(self.db_path, "U-empty")
        self.assertFalse(has_posts(self.db_path, user["id"]))

    def test_has_posts_true_after_save(self):
        user = create_user(self.db_path, "U-poster")
        save_post(self.db_path, user["id"], "text", "hello")
        self.assertTrue(has_posts(self.db_path, user["id"]))

    def test_save_post_returns_id(self):
        user = create_user(self.db_path, "U-saver")
        post_id = save_post(self.db_path, user["id"], "text", "content")
        self.assertGreater(post_id, 0)

    def test_get_recent_posts_returns_latest_first(self):
        user = create_user(self.db_path, "U-recent")
        save_post(self.db_path, user["id"], "text", "first")
        save_post(self.db_path, user["id"], "text", "second")
        save_post(self.db_path, user["id"], "image")
        posts = get_recent_posts(self.db_path, user["id"], limit=2)
        self.assertEqual(len(posts), 2)
        self.assertIsNone(posts[0].get("text"))

    def test_get_recent_posts_excludes_deleted(self):
        user = create_user(self.db_path, "U-deleted")
        save_post(self.db_path, user["id"], "text", "alive")
        from core.database import db_connection

        with db_connection(self.db_path) as db:
            db.execute("UPDATE posts SET status='deleted'")
        posts = get_recent_posts(self.db_path, user["id"])
        self.assertEqual(len(posts), 0)

    def test_get_recent_posts_limited(self):
        user = create_user(self.db_path, "U-limit")
        for i in range(5):
            save_post(self.db_path, user["id"], "text", f"post{i}")
        posts = get_recent_posts(self.db_path, user["id"], limit=3)
        self.assertEqual(len(posts), 3)
        self.assertIn("post4", posts[0]["text"])

    def test_save_media_post(self):
        user = create_user(self.db_path, "U-media")
        post_id = save_post(
            self.db_path, user["id"], "image", media_url="https://example.com/img.jpg", mime_type="image/jpeg"
        )
        from core.database import db_connection

        with db_connection(self.db_path) as db:
            post = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        self.assertEqual(post["media_url"], "https://example.com/img.jpg")
        self.assertEqual(post["mime_type"], "image/jpeg")

    def test_get_user_updates_timestamp(self):
        user = create_user(self.db_path, "U-ts")
        original = user["updated_at"]
        fetched = get_user(self.db_path, "U-ts")
        self.assertNotEqual(fetched["updated_at"], original)


if __name__ == "__main__":
    unittest.main()
