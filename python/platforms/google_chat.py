from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class GoogleChatAdapter(PlatformAdapter):
    """Google Chat app adapter using spaces.messages.create."""
    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["google_chat"]
        self.token = token or os.getenv("GOOGLE_CHAT_ACCESS_TOKEN")
        if not self.token: raise ValueError("GOOGLE_CHAT_ACCESS_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        message = payload.get("message", payload); sender = message.get("sender", {})
        space = payload.get("space", {})
        attachments = message.get("attachment") or message.get("attachments") or []
        attachment = attachments[0] if attachments else {}
        media = attachment.get("downloadUri") or attachment.get("resourceName")
        user_id = sender.get("name") or payload.get("user_id")
        space_name = space.get("name") or payload.get("space_name")
        if not user_id or not space_name:
            raise ValueError("Google Chat event has no sender or space")
        return InboundEvent(platform="google_chat", user_id=str(user_id), reply_target=str(space_name), content_type="file" if media else "text", text=message.get("text"), media_url=media)
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        space = event.reply_target or os.getenv("GOOGLE_CHAT_SPACE")
        if not space: raise ValueError("Google Chat space is required")
        for message in reply.messages:
            response = self.session.post(f"https://chat.googleapis.com/v1/{space}/messages", headers={"Authorization": f"Bearer {self.token}"}, json={"text": message.text or message.media_url or ""}, timeout=30)
            response.raise_for_status()
