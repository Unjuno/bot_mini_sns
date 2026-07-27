from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class TwitchAdapter(PlatformAdapter):
    def __init__(self, token=None, client_id=None, broadcaster_id=None, sender_id=None, session=None):
        self.capabilities = PLATFORM_CATALOG["twitch"]; self.token = token or os.getenv("TWITCH_ACCESS_TOKEN"); self.client_id = client_id or os.getenv("TWITCH_CLIENT_ID"); self.broadcaster_id = broadcaster_id or os.getenv("TWITCH_BROADCASTER_ID"); self.sender_id = sender_id or os.getenv("TWITCH_SENDER_ID")
        if not all((self.token, self.client_id, self.broadcaster_id, self.sender_id)): raise ValueError("TWITCH_ACCESS_TOKEN, TWITCH_CLIENT_ID, TWITCH_BROADCASTER_ID and TWITCH_SENDER_ID are required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        event = payload.get("event", payload)
        return InboundEvent(platform="twitch", user_id=str(event.get("chatter_user_id") or event.get("user_id") or payload.get("user_id")), content_type="text", text=event.get("message", {}).get("text") if isinstance(event.get("message"), dict) else event.get("message") or event.get("text"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        headers = {"Authorization": f"Bearer {self.token}", "Client-Id": self.client_id}
        for message in reply.messages:
            response = self.session.post("https://api.twitch.tv/helix/chat/messages", headers=headers, json={"broadcaster_id": self.broadcaster_id, "sender_id": self.sender_id, "message": message.text or message.media_url or ""}, timeout=30); response.raise_for_status()
