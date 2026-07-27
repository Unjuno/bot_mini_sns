import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with db_connection(db_path) as db:
        existing_posts = {row["name"] for row in db.execute("PRAGMA table_info(posts)")}
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
            legacy_users = db.execute(
                "SELECT user_id, display_name, registered_at FROM users_legacy"
            ).fetchall()
            for lu in legacy_users:
                ts = lu["registered_at"] or now()
                db.execute(
                    "INSERT OR IGNORE INTO users(line_user_id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (lu["user_id"], lu["display_name"], ts, ts),
                )
            legacy_posts = db.execute(
                "SELECT user_id, text, image_path, created_at, package_id, sticker_id FROM posts_legacy"
            ).fetchall()
            for lp in legacy_posts:
                user = db.execute(
                    "SELECT id FROM users WHERE line_user_id=?", (lp["user_id"],)
                ).fetchone()
                if not user:
                    continue
                post_type = "image" if lp["image_path"] else "text"
                db.execute(
                    """INSERT INTO posts(user_id, type, text, media_url, package_id,
                       sticker_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user["id"], post_type, lp["text"], lp["image_path"],
                     lp["package_id"], lp["sticker_id"], lp["created_at"] or now()),
                )


def get_user(db_path: Path, platform_user_id: str) -> dict | None:
    with db_connection(db_path) as db:
        row = db.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (platform_user_id,)
        ).fetchone()
        if row:
            db.execute(
                "UPDATE users SET updated_at=? WHERE line_user_id=?",
                (now(), platform_user_id),
            )
            row = db.execute(
                "SELECT * FROM users WHERE line_user_id = ?", (platform_user_id,)
            ).fetchone()
        return dict(row) if row else None


def create_user(db_path: Path, platform_user_id: str, display_name: str | None = None) -> dict:
    ts = now()
    with db_connection(db_path) as db:
        db.execute(
            "INSERT INTO users(line_user_id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (platform_user_id, display_name, ts, ts),
        )
        row = db.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (platform_user_id,)
        ).fetchone()
        return dict(row)


def ensure_user(db_path: Path, platform_user_id: str) -> dict:
    user = get_user(db_path, platform_user_id)
    if user:
        return user
    return create_user(db_path, platform_user_id)


def has_posts(db_path: Path, user_id: int) -> bool:
    with db_connection(db_path) as db:
        row = db.execute(
            "SELECT 1 FROM posts WHERE user_id=? AND status='published' LIMIT 1",
            (user_id,),
        ).fetchone()
        return row is not None


def save_post(
    db_path: Path,
    user_id: int,
    post_type: str,
    text: str | None = None,
    media_url: str | None = None,
    mime_type: str | None = None,
    duration_ms: int | None = None,
) -> int:
    ts = now()
    with db_connection(db_path) as db:
        cursor = db.execute(
            """INSERT INTO posts(user_id, type, text, media_url, mime_type, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, post_type, text, media_url, mime_type, duration_ms, ts),
        )
        return cursor.lastrowid


def get_recent_posts(db_path: Path, user_id: int, limit: int = 10) -> list[dict]:
    with db_connection(db_path) as db:
        rows = db.execute(
            """SELECT type, text, media_url, created_at
               FROM posts WHERE user_id=? AND status='published'
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
