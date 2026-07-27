from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class RedditAdapter(PlatformAdapter):
    def __init__(self, token=None, session=None):
        self.capabilities = PLATFORM_CATALOG["reddit"]; self.token = token or os.getenv("REDDIT_ACCESS_TOKEN")
        if not self.token: raise ValueError("REDDIT_ACCESS_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        data = payload.get("data", payload); body = data.get("body") or data.get("title") or data.get("text")
        return InboundEvent(platform="reddit", user_id=str(data.get("author", {}).get("name") or data.get("author") or payload.get("user_id")), content_type="text", text=body, media_url=data.get("name") or data.get("id"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        thing_id = event.media_url or os.getenv("REDDIT_THING_ID")
        if not thing_id: raise ValueError("REDDIT_THING_ID is required for replies")
        for message in reply.messages:
            response = self.session.post("https://oauth.reddit.com/api/comment", headers={"Authorization": f"Bearer {self.token}", "User-Agent": "mini-sns-bot/1.0"}, data={"api_type": "json", "thing_id": thing_id, "text": message.text or message.media_url or ""}, timeout=30); response.raise_for_status()
