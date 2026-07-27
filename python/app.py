import json
import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, request, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    AudioMessage,
    AudioSendMessage,
    FileMessage,
    ImageMessage,
    ImageSendMessage,
    MessageEvent,
    TextMessage,
    TextSendMessage,
    VideoMessage,
    VideoSendMessage,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env", override=True)
def project_path(value, default):
    path = Path(value or default)
    return path if path.is_absolute() else ROOT / path


CONFIG_PATH = project_path(os.getenv("CONFIG_PATH"), ROOT / "config.json")
DATABASE_PATH = project_path(os.getenv("DATABASE_PATH"), ROOT / "sns_bot.db")
MEDIA_DIR = project_path(os.getenv("MEDIA_DIR"), ROOT / "uploaded_media")


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as file:
        config = json.load(file)
    config.setdefault("features", {})
    config.setdefault("media", {})
    return config


config = load_config()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with db_connection() as db:
        existing_posts = {
            row["name"] for row in db.execute("PRAGMA table_info(posts)")
        }
        if existing_posts and "type" not in existing_posts:
            db.execute("ALTER TABLE users RENAME TO users_legacy")
            db.execute("ALTER TABLE posts RENAME TO posts_legacy")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_user_id TEXT UNIQUE NOT NULL,
                display_name TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                text TEXT,
                media_url TEXT,
                mime_type TEXT,
                duration_ms INTEGER,
                address TEXT,
                latitude REAL,
                longitude REAL,
                package_id TEXT,
                sticker_id TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS post_reads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                read_at TEXT NOT NULL,
                UNIQUE(post_id, user_id)
            );
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(posts)")}
        for column in ("package_id", "sticker_id"):
            if column not in columns:
                db.execute(f"ALTER TABLE posts ADD COLUMN {column} TEXT")
        if existing_posts and "type" not in existing_posts:
            legacy_users = db.execute("SELECT user_id, display_name, registered_at FROM users_legacy").fetchall()
            for legacy_user in legacy_users:
                timestamp = legacy_user["registered_at"] or now()
                db.execute(
                    "INSERT OR IGNORE INTO users(line_user_id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (legacy_user["user_id"], legacy_user["display_name"], timestamp, timestamp),
                )
            legacy_posts = db.execute(
                "SELECT user_id, text, image_path, created_at, package_id, sticker_id FROM posts_legacy"
            ).fetchall()
            for legacy_post in legacy_posts:
                user = db.execute(
                    "SELECT id FROM users WHERE line_user_id=?", (legacy_post["user_id"],)
                ).fetchone()
                if not user:
                    continue
                post_type = "image" if legacy_post["image_path"] else "text"
                db.execute(
                    """INSERT INTO posts(user_id, type, text, media_url, package_id,
                       sticker_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user["id"], post_type, legacy_post["text"], legacy_post["image_path"],
                     legacy_post["package_id"], legacy_post["sticker_id"], legacy_post["created_at"] or now()),
                )


init_db()


def feature_enabled(name):
    return bool(config["features"].get(name, False))


def get_user(event):
    line_user_id = event.source.user_id
    display_name = getattr(getattr(event, "source", None), "user_id", None)
    with db_connection() as db:
        user = db.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (line_user_id,)
        ).fetchone()
        if user:
            db.execute(
                "UPDATE users SET updated_at=? WHERE line_user_id=?",
                (now(), line_user_id),
            )
            user = db.execute(
                "SELECT * FROM users WHERE line_user_id = ?", (line_user_id,)
            ).fetchone()
            return user
        timestamp = now()
        db.execute(
            "INSERT INTO users(line_user_id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (line_user_id, display_name, timestamp, timestamp),
        )
        return db.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (line_user_id,)
        ).fetchone()


def media_type_enabled(media_type):
    return media_type in config["media"].get("enabled_types", [])


def save_line_content(message, media_type, extension):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{message.id}.{extension}"
    path = MEDIA_DIR / filename
    content = line_bot_api.get_message_content(message.id)
    with path.open("wb") as file:
        for chunk in content.iter_content():
            file.write(chunk)
    return filename


def media_url(filename):
    base_url = os.getenv("MEDIA_BASE_URL", "").rstrip("/")
    return f"{base_url}/media/{filename}" if base_url else None


def save_post(user_id, post_type, message_text=None, **extra):
    with db_connection() as db:
        cursor = db.execute(
            """INSERT INTO posts(user_id, type, text, media_url, mime_type,
               duration_ms, address, latitude, longitude, package_id, sticker_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                post_type,
                message_text,
                extra.get("media_url"),
                extra.get("mime_type"),
                extra.get("duration_ms"),
                extra.get("address"),
                extra.get("latitude"),
                extra.get("longitude"),
                extra.get("package_id"),
                extra.get("sticker_id"),
                now(),
            ),
        )
        return cursor.lastrowid


def reply(event, text):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))


def reply_error(event, message="処理中にエラーが発生しました。もう一度お試しください。"):
    try:
        reply(event, message)
    except Exception:
        app.logger.exception("Failed to send error reply")


def handle_processing_error(event, error, context):
    app.logger.exception("%s failed: %s", context, error)
    reply_error(event)


def recent_posts(user_id, post_type, limit=5):
    with db_connection() as db:
        return db.execute(
            """SELECT type, text, media_url, duration_ms FROM posts
               WHERE user_id=? AND type=? AND status='published'
               ORDER BY id DESC LIMIT ?""",
            (user_id, post_type, limit),
        ).fetchall()


def reply_same_type(event, posts):
    """Send same-type recent content in one LINE reply request."""
    messages = []
    post_type = posts[0]["type"] if posts else None
    if post_type == "file":
        messages = [
            TextSendMessage(text=post["media_url"][:5000])
            for post in posts[:5]
            if post["media_url"]
        ]
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            reply(event, "返信できるコンテンツがありません。")
        return
    for post in posts[:5]:
        url = post["media_url"]
        if post_type == "image" and url:
            messages.append(ImageSendMessage(original_content_url=url, preview_image_url=url))
        elif post_type == "audio" and url and post["duration_ms"] is not None:
            messages.append(AudioSendMessage(original_content_url=url, duration=post["duration_ms"]))
        elif post_type == "video" and url:
            messages.append(VideoSendMessage(original_content_url=url, preview_image_url=url))
    if messages:
        line_bot_api.reply_message(event.reply_token, messages)
    else:
        reply(event, "返信できるコンテンツがありません。")


def usage_text():
    return (
        "文章、写真、音声、動画、ファイルを送信できます。"
    )


def has_posts(user_id):
    with db_connection() as db:
        return db.execute("SELECT 1 FROM posts WHERE user_id=? AND status='published' LIMIT 1", (user_id,)).fetchone() is not None


def saved_posts_text(user_id, limit=10):
    with db_connection() as db:
        posts = db.execute("SELECT type, text FROM posts WHERE user_id=? AND status='published' ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    labels = {"text": "文章", "image": "写真", "audio": "音声", "video": "動画", "file": "ファイル"}
    lines = ["保存済みの投稿:"]
    for post in posts:
        value = (post["text"] or "").replace("\n", " ").strip()
        lines.append(f"・{labels.get(post['type'], post['type'])}" + (f": {value[:80]}" if value else ""))
    return "\n".join(lines) if lines else "保存済みの投稿はありません。"


@app.route("/")
def index():
    return "LINE mini SNS is running"


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_DIR, filename)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception:
        app.logger.exception("Webhook processing failed")
        abort(500)
    return "OK"


def ensure_active(event):
    user = get_user(event)
    if not user or user["status"] != "active":
        reply(event, "この投稿を受け付けられません。")
        return None
    return user


@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    try:
        text = event.message.text.strip()
        user = ensure_active(event)
        if not user:
            return
        if not feature_enabled("text_post"):
            reply(event, "テキスト投稿は現在利用できません。")
            return
        if not text:
            reply(event, "空の投稿はできません。")
            return
        save_post(user["id"], "text", text)
        posts = recent_posts(user["id"], "text")
        messages = [
            TextSendMessage(text=post["text"][:5000])
            for post in posts[:5]
            if post["text"]
        ]
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            reply(event, "返信できる文章がありません。")
    except Exception as error:
        handle_processing_error(event, error, "text message")


def handle_media(event, message, media_type, extension, mime_type):
    try:
        user = ensure_active(event)
        if not user:
            return
        if not media_type_enabled(media_type):
            reply(event, f"{media_type}の投稿は現在利用できません。")
            return
        if not os.getenv("MEDIA_BASE_URL", "").strip():
            reply(event, "メディア返信の設定が完了していません。管理者に連絡してください。")
            return
        filename = save_line_content(message, media_type, extension)
        saved_media_url = media_url(filename)
        duration_ms = getattr(message, "duration", None)
        save_post(user["id"], media_type, media_url=saved_media_url, mime_type=mime_type,
                  duration_ms=duration_ms)
        reply_same_type(event, recent_posts(user["id"], media_type))
    except Exception as error:
        handle_processing_error(event, error, f"{media_type} message")


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    handle_media(event, event.message, "image", "jpg", "image/jpeg")


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    handle_media(event, event.message, "audio", "m4a", "audio/m4a")


@handler.add(MessageEvent, message=VideoMessage)
def handle_video(event):
    handle_media(event, event.message, "video", "mp4", "video/mp4")


@handler.add(MessageEvent, message=FileMessage)
def handle_file(event):
    handle_media(event, event.message, "file", "bin", "application/octet-stream")


@handler.default()
def handle_unsupported_event(event):
    """Reply instead of silently ignoring unsupported LINE events/content."""
    message = getattr(event, "message", None)
    content_type = getattr(message, "type", "この種類")
    reply(event, f"申し訳ありません。「{content_type}」には対応していません。")



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
