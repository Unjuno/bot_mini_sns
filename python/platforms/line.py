from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class LineAdapter(PlatformAdapter):
    """LINE Messaging API adapter using the webhook event's reply token."""
    def __init__(self, access_token=None, session=None):
        self.capabilities = PLATFORM_CATALOG["line"]; self.access_token = access_token or os.getenv("ACCESS_TOKEN")
        if not self.access_token: raise ValueError("ACCESS_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        event = (payload.get("events") or [payload])[0]; message = event.get("message", {}); kind = {"text": "text", "image": "image", "audio": "audio", "video": "video", "file": "file"}.get(message.get("type"), "text")
        source = event.get("source", {}); return InboundEvent(platform="line", user_id=str(source.get("userId") or payload.get("user_id")), content_type=kind, text=message.get("text"), media_url=message.get("id"), reply_token=event.get("replyToken"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        if not event.reply_token:
            raise ValueError("LINE reply_token is required for replies")
        messages = [{"type": "text", "text": message.text or message.media_url or ""} for message in reply.messages[:5]]
        response = self.session.post("https://api.line.me/v2/bot/message/reply", headers={"Authorization": f"Bearer {self.access_token}"}, json={"replyToken": event.reply_token, "messages": messages}, timeout=30); response.raise_for_status()
