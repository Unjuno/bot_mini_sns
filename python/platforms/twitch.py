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
        user_id = event.get("chatter_user_id") or event.get("user_id") or payload.get("user_id")
        if not user_id:
            raise ValueError("Twitch event has no chatter user")
        text = event.get("message", {}).get("text") if isinstance(event.get("message"), dict) else event.get("message") or event.get("text")
        if text is None:
            raise ValueError("Twitch event has no chat message")
        return InboundEvent(platform="twitch", user_id=str(user_id), reply_to_id=event.get("message_id"), content_type="text", text=text)
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        headers = {"Authorization": f"Bearer {self.token}", "Client-Id": self.client_id}
        for message in reply.messages:
            body = {"broadcaster_id": self.broadcaster_id, "sender_id": self.sender_id, "message": message.text or message.media_url or ""}
            if event.reply_to_id:
                body["reply_parent_message_id"] = event.reply_to_id
            response = self.session.post("https://api.twitch.tv/helix/chat/messages", headers=headers, json=body, timeout=30); response.raise_for_status()
            result = response.json()
            if not result.get("data") or not result["data"][0].get("is_sent"):
                raise RuntimeError(f"Twitch chat message was not sent: {result}")
