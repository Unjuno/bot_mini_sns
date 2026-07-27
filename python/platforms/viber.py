from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class ViberAdapter(PlatformAdapter):
    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["viber"]; self.token = token or os.getenv("VIBER_AUTH_TOKEN")
        if not self.token: raise ValueError("VIBER_AUTH_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        sender = payload.get("sender", {}); message = payload.get("message", {}); kind = message.get("type", "text")
        kind = kind if kind in ("text", "image", "video", "file", "audio") else "text"
        return InboundEvent(platform="viber", user_id=str(sender.get("id") or payload.get("user_id")), content_type=kind, text=message.get("text"), media_url=message.get("media"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages:
            body = {"receiver": event.user_id, "type": message.type}
            if message.type == "text":
                body["text"] = message.text
            else:
                if message.type == "audio":
                    raise ValueError("Viber audio replies are not supported by the documented Bot API types")
                if not message.media_url:
                    raise ValueError(f"Viber {message.type} reply requires media_url")
                body["media"] = message.media_url
                if message.text:
                    body["text"] = message.text
            response = self.session.post("https://chatapi.viber.com/pa/send_message", headers={"X-Viber-Auth-Token": self.token}, json=body, timeout=30); response.raise_for_status()
