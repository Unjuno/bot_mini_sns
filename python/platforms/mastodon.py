from __future__ import annotations

import os
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class MastodonAdapter(PlatformAdapter):
    capabilities = PLATFORM_CATALOG["mastodon"]

    def __init__(self, base_url: str | None = None, token: str | None = None, session: requests.Session | None = None):
        self.base_url = (base_url or os.getenv("MASTODON_BASE_URL", "")).rstrip("/")
        self.token = token or os.getenv("MASTODON_ACCESS_TOKEN")
        if not self.base_url or not self.token:
            raise ValueError("MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN are required")
        self.session = session or requests.Session()

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        status = payload.get("status", payload)
        account = status.get("account", {})
        user_id = str(account.get("id") or status.get("account_id", ""))
        if not user_id:
            raise ValueError("Mastodon status has no account")
        attachments = status.get("media_attachments") or []
        common = {"platform": "mastodon", "user_id": user_id}
        if status.get("text"):
            return InboundEvent(**common, content_type="text", text=status["text"])
        if attachments:
            attachment = attachments[0]
            return InboundEvent(**common, content_type=self._content_type(attachment.get("type", "")), media_url=attachment.get("url"))
        raise ValueError("Mastodon status has no supported content")

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        headers = {"Authorization": f"Bearer {self.token}"}
        for message in reply.messages[: self.capabilities.max_reply_items or len(reply.messages)]:
            response = self.session.post(
                f"{self.base_url}/api/v1/statuses",
                headers=headers,
                data={"status": (message.text or message.media_url or "")[:5000]},
                timeout=30,
            )
            response.raise_for_status()

    @staticmethod
    def _content_type(value: str) -> str:
        return {"image": "image", "audio": "audio", "video": "video"}.get(value, "file")
