from __future__ import annotations

import os
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class MisskeyAdapter(PlatformAdapter):
    """Misskey HTTP API adapter for notes and note media links."""

    capabilities = PLATFORM_CATALOG["misskey"]

    def __init__(self, base_url: str | None = None, token: str | None = None, session: requests.Session | None = None):
        self.base_url = (base_url or os.getenv("MISSKEY_BASE_URL", "")).rstrip("/")
        self.token = token or os.getenv("MISSKEY_TOKEN")
        if not self.base_url or not self.token:
            raise ValueError("MISSKEY_BASE_URL and MISSKEY_TOKEN are required")
        self.session = session or requests.Session()

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        note = payload.get("body", payload.get("note", payload))
        user_id = str(note.get("userId") or note.get("user", {}).get("id", ""))
        if not user_id:
            raise ValueError("Misskey note has no user")
        files = note.get("files") or []
        common = {"platform": "misskey", "user_id": user_id, "reply_to_id": str(note.get("id")) if note.get("id") else None}
        if note.get("text"):
            return InboundEvent(**common, content_type="text", text=note["text"])
        if files:
            file = files[0]
            content_type = self._content_type(file.get("type", ""))
            return InboundEvent(**common, content_type=content_type, media_url=file.get("url"))
        raise ValueError("Misskey note has no supported content")

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages[: self.capabilities.max_reply_items or len(reply.messages)]:
            text = message.text or message.media_url or ""
            response = self.session.post(
                f"{self.base_url}/api/notes/create",
                json={"i": self.token, "text": text[:3000], **({"replyId": event.reply_to_id} if event.reply_to_id else {})},
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
            if body.get("error"):
                raise RuntimeError(f"Misskey API error: {body['error']}")

    @staticmethod
    def _content_type(mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("video/"):
            return "video"
        return "file"
