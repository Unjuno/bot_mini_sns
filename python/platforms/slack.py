from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class SlackAdapter(PlatformAdapter):
    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["slack"]; self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token: raise ValueError("SLACK_BOT_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        event = payload.get("event", payload); files = event.get("files") or []; file = files[0] if files else {}
        kind = {"image": "image", "audio": "audio", "video": "video"}.get(file.get("filetype"), "file" if file else "text")
        user_id = event.get("user") or event.get("user_id")
        channel_id = event.get("channel") or event.get("channel_id")
        if not user_id or not channel_id:
            raise ValueError("Slack event has no user or channel")
        return InboundEvent(platform="slack", user_id=str(user_id), reply_target=str(channel_id), content_type=kind, text=event.get("text"), media_url=file.get("url_private"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages:
            response = self.session.post("https://slack.com/api/chat.postMessage", headers={"Authorization": f"Bearer {self.token}"}, json={"channel": event.reply_target or event.user_id, "text": message.text or message.media_url or ""}, timeout=30)
            response.raise_for_status()
            if response.json().get("ok") is False: raise ValueError(response.json().get("error", "Slack API error"))
