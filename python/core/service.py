from __future__ import annotations

from dataclasses import dataclass, field
import sqlite3
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
