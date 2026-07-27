from __future__ import annotations

from dataclasses import dataclass, field
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
        return [
            post for post in self.posts
            if post.platform == platform
            and post.user_id == user_id
            and post.content_type == content_type
        ][:limit]


def process_event(
    event: InboundEvent,
    repository: PostRepository,
    max_reply_items: int = 5,
) -> OutboundReply:
    """Persist an event and build a same-type reply without platform APIs."""
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
