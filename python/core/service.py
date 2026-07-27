from __future__ import annotations

from dataclasses import dataclass, field
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Protocol

from .models import InboundEvent, OutboundMessage, OutboundReply


@dataclass
class StoredPost:
    platform: str
    user_id: str
    content_type: str
    text: str | None = None
    media_url: str | None = None
    duration_ms: int | None = None


class PostRepository(Protocol):
    def save(self, post: StoredPost) -> None: ...

    def recent(self, platform: str, user_id: str, content_type: str, limit: int) -> list[StoredPost]: ...


@dataclass
class MemoryPostRepository:
    posts: list[StoredPost] = field(default_factory=list)

    def save(self, post: StoredPost) -> None:
        self.posts.insert(0, post)

    def recent(self, platform: str, user_id: str, content_type: str, limit: int) -> list[StoredPost]:
        return [post for post in self.posts if post.content_type == content_type][:limit]


class SQLitePostRepository:
    """Persistent repository used by the platform-neutral webhook server."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS platform_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    text TEXT,
                    media_url TEXT,
                    created_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS processed_events (
                    fingerprint TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def claim_event(self, fingerprint: str) -> dict | None:
        """Return the previous response for a duplicate, otherwise reserve it."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response_json FROM processed_events WHERE fingerprint=?",
                (fingerprint,),
            ).fetchone()
            if row:
                return json.loads(row[0])
            connection.execute(
                "INSERT INTO processed_events (fingerprint, response_json, created_at) VALUES (?, ?, ?)",
                (fingerprint, json.dumps({"messages": []}), datetime.now(timezone.utc).isoformat()),
            )
        return None

    def complete_event(self, fingerprint: str, response: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE processed_events SET response_json=? WHERE fingerprint=?",
                (json.dumps(response), fingerprint),
            )

    def save(self, post: StoredPost) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO platform_posts
                   (platform, user_id, content_type, text, media_url, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (post.platform, post.user_id, post.content_type, post.text,
                 post.media_url, datetime.now(timezone.utc).isoformat()),
            )

    def recent(self, platform: str, user_id: str, content_type: str, limit: int) -> list[StoredPost]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT platform, user_id, content_type, text, media_url
                   FROM platform_posts
                   WHERE content_type=?
                   ORDER BY id DESC LIMIT ?""",
                (content_type, limit),
            ).fetchall()
        return [StoredPost(*row) for row in rows]

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class PostgresPostRepository:
    """PostgreSQL repository for multi-process or ephemeral deployments.

    psycopg is imported lazily so SQLite-only local installations stay lightweight.
    """

    def __init__(self, url: str):
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("DATABASE_URL requires the optional 'psycopg[binary]' package") from error
        self._psycopg = psycopg
        self.url = url
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS platform_posts (
                        id BIGSERIAL PRIMARY KEY, platform TEXT NOT NULL,
                        user_id TEXT NOT NULL, content_type TEXT NOT NULL,
                        text TEXT, media_url TEXT, status TEXT NOT NULL DEFAULT 'published',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )"""
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS platform_posts_content_type_id_idx ON platform_posts (content_type, id DESC)")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS processed_events (
                        fingerprint TEXT PRIMARY KEY, response_json TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )"""
                )

    @contextmanager
    def _connect(self):
        connection = self._psycopg.connect(self.url)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def claim_event(self, fingerprint: str) -> dict | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT response_json FROM processed_events WHERE fingerprint=%s", (fingerprint,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            cursor.execute("INSERT INTO processed_events (fingerprint, response_json) VALUES (%s, %s)", (fingerprint, json.dumps({"messages": []})))
        return None

    def complete_event(self, fingerprint: str, response: dict) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE processed_events SET response_json=%s WHERE fingerprint=%s", (json.dumps(response), fingerprint))

    def save(self, post: StoredPost) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("INSERT INTO platform_posts (platform,user_id,content_type,text,media_url) VALUES (%s,%s,%s,%s,%s)", (post.platform, post.user_id, post.content_type, post.text, post.media_url))

    def recent(self, platform: str, user_id: str, content_type: str, limit: int) -> list[StoredPost]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT platform,user_id,content_type,text,media_url FROM platform_posts WHERE content_type=%s AND status='published' ORDER BY id DESC LIMIT %s", (content_type, limit))
            rows = cursor.fetchall()
        return [StoredPost(*row) for row in rows]


def process_event(
    event: InboundEvent,
    repository: PostRepository,
    max_reply_items: int = 5,
) -> OutboundReply:
    """Persist an event and build a cross-platform same-type feed reply."""
    repository.save(
        StoredPost(
            platform=event.platform,
            user_id=event.user_id,
            content_type=event.content_type,
            text=event.text,
            media_url=event.media_url,
        )
    )
    posts = repository.recent(
        event.platform, event.user_id, event.content_type, max_reply_items
    )
    messages = [
        OutboundMessage(
            type=post.content_type,
            text=post.text or "",
            media_url=post.media_url,
        )
        for post in posts
    ]
    return OutboundReply(messages=messages)
