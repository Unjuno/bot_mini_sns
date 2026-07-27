from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class KakaoTalkAdapter(PlatformAdapter):
    """Kakao i Open Builder skill adapter; replies are posted to the configured callback."""
    def __init__(self, callback_url=None, session=None):
        self.capabilities = PLATFORM_CATALOG["kakaotalk"]; self.callback_url = callback_url or os.getenv("KAKAOTALK_CALLBACK_URL")
        if not self.callback_url: raise ValueError("KAKAOTALK_CALLBACK_URL is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        user = payload.get("userRequest", {}); utterance = user.get("utterance", ""); user_id = user.get("user", {}).get("id") or payload.get("user_id")
        return InboundEvent(platform="kakaotalk", user_id=str(user_id), content_type="text", text=utterance)
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        outputs = [{"simpleText": {"text": message.text or message.media_url or ""}} for message in reply.messages]
        response = self.session.post(self.callback_url, json={"version": "2.0", "template": {"outputs": outputs}}, timeout=30); response.raise_for_status()
