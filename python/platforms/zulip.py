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
        user_id = message.get("sender_email") or message.get("sender_id")
        if not user_id:
            raise ValueError("Zulip message has no sender")
        if message.get("type") == "stream":
            stream = message.get("display_recipient")
            subject = message.get("subject")
            if not stream or not subject:
                raise ValueError("Zulip stream message has no stream or subject")
            return InboundEvent(platform="zulip", user_id=str(user_id), reply_target=str(stream), reply_to_id=str(subject), reply_mode="stream", content_type="text", text=message.get("content") or message.get("text"))
        return InboundEvent(platform="zulip", user_id=str(user_id), reply_mode="direct", content_type="text", text=message.get("content") or message.get("text"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages:
            if event.reply_mode == "stream":
                data = {"type": "stream", "to": event.reply_target, "subject": event.reply_to_id, "content": message.text or message.media_url or ""}
            else:
                data = {"type": "direct", "to": event.user_id, "content": message.text or message.media_url or ""}
            response = self.session.post(f"{self.base_url}/api/v1/messages", data=data, auth=(self.email, self.api_key), timeout=30)
            response.raise_for_status()
