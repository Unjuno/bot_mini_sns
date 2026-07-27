import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


# app.py reads these values during import. Tests use harmless placeholders.
os.environ.setdefault("ACCESS_TOKEN", "test-access-token")
os.environ.setdefault("CHANNEL_SECRET", "test-channel-secret")

import app


class MiniSNSAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.database_path = Path(cls.temp_dir.name) / "test.db"
        cls.media_dir = Path(cls.temp_dir.name) / "media"
        app.DATABASE_PATH = cls.database_path
        app.MEDIA_DIR = cls.media_dir
        app.init_db()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        with app.db_connection() as db:
            db.execute("DELETE FROM post_reads")
            db.execute("DELETE FROM posts")
            db.execute("DELETE FROM users")

    def test_database_schema_is_created(self):
        with app.db_connection() as db:
            tables = {
                row["name"]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            columns = {
                row["name"] for row in db.execute("PRAGMA table_info(posts)")
            }
        self.assertTrue({"users", "posts", "post_reads"}.issubset(tables))
        self.assertTrue({"type", "package_id", "sticker_id"}.issubset(columns))

    def test_post_can_be_saved_and_read(self):
        with app.db_connection() as db:
            db.execute(
                """INSERT INTO users(line_user_id, display_name, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                ("U-test", "Test User", app.now(), app.now()),
            )
            user_id = db.execute(
                "SELECT id FROM users WHERE line_user_id=?", ("U-test",)
            ).fetchone()["id"]

        post_id = app.save_post(user_id, "text", "Hello community")

        with app.db_connection() as db:
            post = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        self.assertEqual(post["type"], "text")
        self.assertEqual(post["text"], "Hello community")

    def test_empty_user_has_no_posts_and_saved_summary_is_updated(self):
        with app.db_connection() as db:
            db.execute(
                "INSERT INTO users(line_user_id, created_at, updated_at) VALUES (?, ?, ?)",
                ("U-empty", app.now(), app.now()),
            )
            user_id = db.execute(
                "SELECT id FROM users WHERE line_user_id=?", ("U-empty",)
            ).fetchone()["id"]
        self.assertFalse(app.has_posts(user_id))
        app.save_post(user_id, "text", "最初の投稿")
        self.assertTrue(app.has_posts(user_id))
        self.assertIn("最初の投稿", app.saved_posts_text(user_id))

    def test_enabled_media_types_are_configurable(self):
        original_types = app.config["media"]["enabled_types"]
        app.config["media"]["enabled_types"] = ["image", "sticker"]
        try:
            self.assertTrue(app.media_type_enabled("image"))
            self.assertTrue(app.media_type_enabled("sticker"))
            self.assertFalse(app.media_type_enabled("audio"))
        finally:
            app.config["media"]["enabled_types"] = original_types

    def test_health_endpoint(self):
        response = app.app.test_client().get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("LINE mini SNS", response.get_data(as_text=True))

    def test_reply_builds_text_message(self):
        event = type("Event", (), {"reply_token": "reply-token"})()
        original_reply_message = app.line_bot_api.reply_message
        calls = []
        app.line_bot_api.reply_message = lambda token, message: calls.append((token, message))
        try:
            app.reply(event, "テスト返信")
        finally:
            app.line_bot_api.reply_message = original_reply_message

        self.assertEqual(calls[0][0], "reply-token")
        self.assertEqual(calls[0][1].text, "テスト返信")

    def test_media_endpoint_returns_404_for_missing_file(self):
        response = app.app.test_client().get("/media/not-found.jpg")
        self.assertEqual(response.status_code, 404)

    def test_admin_can_soft_delete_post_only_with_token(self):
        with app.db_connection() as db:
            db.execute(
                "INSERT INTO users(line_user_id, created_at, updated_at) VALUES (?, ?, ?)",
                ("admin-test-user", app.now(), app.now()),
            )
            user = db.execute("SELECT id FROM users WHERE line_user_id=?", ("admin-test-user",)).fetchone()
        post_id = app.save_post(user["id"], "text", "remove me")
        previous = os.environ.get("ADMIN_TOKEN")
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        try:
            client = app.app.test_client()
            self.assertEqual(client.delete(f"/admin/posts/{post_id}").status_code, 403)
            response = client.delete(
                f"/admin/posts/{post_id}",
                headers={"Authorization": "Bearer test-admin-token"},
            )
            self.assertEqual(response.status_code, 200)
            with app.db_connection() as db:
                status = db.execute("SELECT status FROM posts WHERE id=?", (post_id,)).fetchone()["status"]
            self.assertEqual(status, "deleted")
        finally:
            if previous is None:
                os.environ.pop("ADMIN_TOKEN", None)
            else:
                os.environ["ADMIN_TOKEN"] = previous


if __name__ == "__main__":
    unittest.main()
