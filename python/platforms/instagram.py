from __future__ import annotations
import os

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class InstagramAdapter(PlatformAdapter):
    """Instagram Messaging API adapter for Professional-account DMs."""

    capabilities = PLATFORM_CATALOG["instagram"]

    def __init__(self, token=None, instagram_account_id=None, session=None):
        self.token = token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = instagram_account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        if not self.token or not self.instagram_account_id:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID are required")
        self.session = session or requests.Session()

    def parse_event(self, payload, headers=None):
        messaging = (payload.get("entry") or [{}])[0].get("messaging") or []
        event = messaging[0] if messaging else payload
        message = event.get("message") or payload.get("message") or {}
        sender = event.get("sender") or payload.get("sender") or {}
        if not sender.get("id"):
            raise ValueError("Instagram event has no sender")
        if message.get("text") is not None:
            return InboundEvent(platform="instagram", user_id=str(sender["id"]), content_type="text", text=message["text"])
        attachments = message.get("attachments") or []
        if attachments:
            attachment = attachments[0]
            attachment_type = attachment.get("type", "file")
            content_type = attachment_type if attachment_type in ("image", "audio", "video", "file") else "file"
            return InboundEvent(platform="instagram", user_id=str(sender["id"]), content_type=content_type, media_url=attachment.get("payload", {}).get("url"))
        raise ValueError("Instagram event has no supported message")

    def send_reply(self, event, reply):
        for message in reply.messages:
            body = {"recipient": {"id": event.user_id}}
            if message.type == "text":
                body["message"] = {"text": message.text}
            else:
                if not message.media_url:
                    raise ValueError(f"Instagram {message.type} reply requires media_url")
                body["message"] = {"attachment": {"type": message.type, "payload": {"url": message.media_url}}}
            response = self.session.post(f"https://graph.facebook.com/v20.0/{self.instagram_account_id}/messages", headers={"Authorization": f"Bearer {self.token}"}, json=body, timeout=30)
            response.raise_for_status()
