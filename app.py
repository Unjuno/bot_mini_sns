import json
import os
import sqlite3
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
    LocationMessage,
    LocationSendMessage,
    MessageEvent,
    StickerMessage,
    StickerSendMessage,
    TextMessage,
    TextSendMessage,
    VideoMessage,
    VideoSendMessage,
)

load_dotenv(override=True)

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", ROOT / "config.json"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", ROOT / "sns_bot.db"))
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", ROOT / "uploaded_media"))


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as file:
        config = json.load(file)
    config.setdefault("features", {})
    config.setdefault("timeline", {})
    config.setdefault("media", {})
    return config


config = load_config()
app = Flask(__name__)
line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


def now():
    return datetime.now(timezone.utc).isoformat()


def db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db_connection() as db:
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
            return user
        if not feature_enabled("registration"):
            return None
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
    return "OK"


def ensure_active(event):
    user = get_user(event)
    if not user or user["status"] != "active":
        reply(event, "登録が必要です。まず「登録」と送信してください。")
        return None
    return user


@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()
    if text == "登録":
        user = get_user(event)
        if user:
            reply(event, "登録されています。テキストや対応しているコンテンツを投稿できます。")
        else:
            reply(event, "現在、新規登録を受け付けていません。")
        return
    if text == "退会":
        with db_connection() as db:
            db.execute("UPDATE users SET status='deleted', updated_at=? WHERE line_user_id=?", (now(), event.source.user_id))
        reply(event, "退会しました。")
        return
    if text in {"使い方", "ヘルプ"}:
        reply(event, "投稿はそのまま送信してください。新着投稿を見るときは「新着」と送信してください。")
        return
    if text in {"新着", "タイムライン"}:
        fetch_posts(event)
        return
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
    reply(event, "投稿しました。")


def handle_media(event, message, media_type, extension, mime_type):
    user = ensure_active(event)
    if not user:
        return
    if not media_type_enabled(media_type):
        reply(event, f"{media_type}の投稿は現在利用できません。")
        return
    filename = save_line_content(message, media_type, extension)
    save_post(user["id"], media_type, media_url=media_url(filename), mime_type=mime_type,
              duration_ms=getattr(message, "duration", None))
    reply(event, f"{media_type}を投稿しました。")


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


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user = ensure_active(event)
    if not user:
        return
    if not media_type_enabled("location"):
        reply(event, "位置情報の投稿は現在利用できません。")
        return
    save_post(user["id"], "location", event.message.title,
              address=event.message.address, latitude=event.message.latitude,
              longitude=event.message.longitude)
    reply(event, "位置情報を投稿しました。")


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    user = ensure_active(event)
    if not user:
        return
    if not media_type_enabled("sticker"):
        reply(event, "スタンプ投稿は現在利用できません。")
        return
    save_post(user["id"], "sticker", package_id=event.message.package_id,
              sticker_id=event.message.sticker_id)
    reply(event, "スタンプを投稿しました。")


def fetch_posts(event):
    user = ensure_active(event)
    if not user or not feature_enabled("post_fetch"):
        return
    limit = int(config["timeline"].get("posts_per_request", 10))
    include_author = bool(config["timeline"].get("include_author_posts", True))
    with db_connection() as db:
        condition = "" if include_author else "AND p.user_id != ?"
        params = [user["id"]] if include_author else [user["id"], user["id"]]
        posts = db.execute(
            f"""SELECT p.* FROM posts p LEFT JOIN post_reads r
                ON r.post_id=p.id AND r.user_id=?
                WHERE p.status='published' AND r.id IS NULL {condition}
                ORDER BY p.created_at ASC LIMIT ?""",
            params + [limit],
        ).fetchall()
        for post in posts:
            db.execute("INSERT OR IGNORE INTO post_reads(post_id,user_id,read_at) VALUES(?,?,?)", (post["id"], user["id"], now()))
    if not posts:
        reply(event, "新しい投稿はありません。")
        return
    messages = []
    for post in posts:
        if post["type"] == "text":
            messages.append(TextSendMessage(text=post["text"]))
        elif post["type"] == "image" and post["media_url"]:
            messages.append(ImageSendMessage(original_content_url=post["media_url"], preview_image_url=post["media_url"]))
        elif post["type"] == "audio" and post["media_url"]:
            messages.append(AudioSendMessage(original_content_url=post["media_url"], duration=post["duration_ms"] or 1000))
        elif post["type"] == "video" and post["media_url"]:
            messages.append(VideoSendMessage(original_content_url=post["media_url"], preview_image_url=post["media_url"]))
        elif post["type"] == "location":
            messages.append(LocationSendMessage(title=post["text"] or "投稿場所", address=post["address"], latitude=post["latitude"], longitude=post["longitude"]))
        elif post["type"] == "sticker":
            messages.append(StickerSendMessage(package_id=post["package_id"], sticker_id=post["sticker_id"]))
        else:
            messages.append(TextSendMessage(text=post["text"] or f"{post['type']}の投稿: {post['media_url'] or '保存済み'}"))
    line_bot_api.reply_message(event.reply_token, messages[:5])


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
