from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class BlueskyAdapter(PlatformAdapter):
    """AT Protocol adapter for text posts; media URLs use text fallback."""

    capabilities = PLATFORM_CATALOG["bluesky"]

    def __init__(self, service_url: str | None = None, access_jwt: str | None = None, repo: str | None = None, session: requests.Session | None = None):
        self.service_url = (service_url or os.getenv("BLUESKY_SERVICE_URL", "https://bsky.social")).rstrip("/")
        self.access_jwt = access_jwt or os.getenv("BLUESKY_ACCESS_JWT")
        self.repo = repo or os.getenv("BLUESKY_REPO")
        if not self.access_jwt or not self.repo:
            raise ValueError("BLUESKY_ACCESS_JWT and BLUESKY_REPO are required")
        self.session = session or requests.Session()

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        record = payload.get("record", payload)
        author = payload.get("author", payload.get("did", ""))
        text = record.get("text")
        if not author or text is None:
            raise ValueError("Bluesky post has no supported content")
        return InboundEvent(
            platform="bluesky",
            user_id=str(author),
            content_type="text",
            text=text,
            reply_to_uri=payload.get("uri"),
            reply_to_cid=payload.get("cid"),
        )

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        headers = {"Authorization": f"Bearer {self.access_jwt}", "Content-Type": "application/json"}
        for message in reply.messages[: self.capabilities.max_reply_items or len(reply.messages)]:
            record = {
                "text": message.text or message.media_url or "",
                "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            if event.reply_to_uri and event.reply_to_cid:
                record["reply"] = {
                    "root": {"uri": event.reply_to_uri, "cid": event.reply_to_cid},
                    "parent": {"uri": event.reply_to_uri, "cid": event.reply_to_cid},
                }
            response = self.session.post(
                f"{self.service_url}/xrpc/com.atproto.repo.createRecord",
                headers=headers,
                json={"repo": self.repo, "collection": "app.bsky.feed.post", "record": record},
                timeout=30,
            )
            response.raise_for_status()
