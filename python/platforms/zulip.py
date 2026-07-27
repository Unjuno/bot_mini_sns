from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class ZulipAdapter(PlatformAdapter):
    def __init__(self, base_url: str | None = None, email: str | None = None, api_key: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["zulip"]
        self.base_url = (base_url or os.getenv("ZULIP_BASE_URL", "")).rstrip("/")
        self.email = email or os.getenv("ZULIP_EMAIL")
        self.api_key = api_key or os.getenv("ZULIP_API_KEY")
        if not self.base_url or not self.email or not self.api_key: raise ValueError("ZULIP_BASE_URL, ZULIP_EMAIL and ZULIP_API_KEY are required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        message = payload.get("message", payload)
        return InboundEvent(platform="zulip", user_id=str(message.get("sender_email") or message.get("sender_id")), content_type="text", text=message.get("content") or message.get("text"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages:
            response = self.session.post(f"{self.base_url}/api/v1/messages", data={"type": "direct", "to": event.user_id, "content": message.text or message.media_url or ""}, auth=(self.email, self.api_key), timeout=30)
            response.raise_for_status()
