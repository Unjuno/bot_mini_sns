from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class WhatsAppAdapter(PlatformAdapter):
    def __init__(self, token: str | None = None, phone_number_id: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["whatsapp"]; self.token = token or os.getenv("WHATSAPP_ACCESS_TOKEN"); self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        if not self.token or not self.phone_number_id: raise ValueError("WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID are required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        value = (payload.get("entry") or [{}])[0].get("changes", [{}])[0].get("value", payload); message = (value.get("messages") or [{}])[0]
        kind = message.get("type", "text")
        kind = {"text": "text", "image": "image", "audio": "audio", "video": "video", "document": "file"}.get(kind, "text")
        item = message.get("document" if kind == "file" else kind, {})
        return InboundEvent(platform="whatsapp", user_id=str(message.get("from") or payload.get("user_id")), content_type=kind, text=item.get("body") or item.get("caption"), media_url=item.get("id"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        url = f"https://graph.facebook.com/v20.0/{self.phone_number_id}/messages"
        for message in reply.messages:
            body = {"messaging_product": "whatsapp", "to": event.user_id}
            if message.type == "text":
                body.update({"type": "text", "text": {"body": message.text}})
            else:
                media_key = {"image": "image", "audio": "audio", "video": "video", "file": "document"}[message.type]
                if not message.media_url:
                    raise ValueError(f"WhatsApp {message.type} reply requires media_url")
                body["type"] = media_key
                body[media_key] = {"id": message.media_url, **({"caption": message.text} if message.text and media_key in ("image", "video", "document") else {})}
            response = self.session.post(url, headers={"Authorization": f"Bearer {self.token}"}, json=body, timeout=30); response.raise_for_status()
