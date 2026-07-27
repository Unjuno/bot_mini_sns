from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class TeamsAdapter(PlatformAdapter):
    def __init__(self, token=None, session=None):
        self.capabilities = PLATFORM_CATALOG["teams"]; self.token = token or os.getenv("TEAMS_BOT_TOKEN")
        if not self.token: raise ValueError("TEAMS_BOT_TOKEN is required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        attachments = payload.get("attachments") or []; attachment = attachments[0] if attachments else {}
        user_id = payload.get("from", {}).get("id") or payload.get("user_id")
        conversation_id = payload.get("conversation", {}).get("id")
        if not user_id or not conversation_id:
            raise ValueError("Teams activity has no sender or conversation")
        return InboundEvent(platform="teams", user_id=str(user_id), reply_target=str(conversation_id), content_type="file" if attachment else "text", text=payload.get("text"), media_url=attachment.get("contentUrl"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        service_url = os.getenv("TEAMS_SERVICE_URL"); conversation_id = event.reply_target or os.getenv("TEAMS_CONVERSATION_ID")
        if not conversation_id: raise ValueError("Teams conversation ID is required")
        if not service_url: raise ValueError("TEAMS_SERVICE_URL is required")
        for message in reply.messages:
            response = self.session.post(f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities", headers={"Authorization": f"Bearer {self.token}"}, json={"type": "message", "text": message.text or message.media_url or ""}, timeout=30); response.raise_for_status()
