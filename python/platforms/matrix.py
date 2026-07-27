from __future__ import annotations
import os
from typing import Any
import requests
from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG

class MatrixAdapter(PlatformAdapter):
    def __init__(self, base_url: str | None = None, access_token: str | None = None, session: requests.Session | None = None):
        self.capabilities = PLATFORM_CATALOG["matrix"]
        self.base_url = (base_url or os.getenv("MATRIX_BASE_URL", "")).rstrip("/")
        self.access_token = access_token or os.getenv("MATRIX_ACCESS_TOKEN")
        if not self.base_url or not self.access_token: raise ValueError("MATRIX_BASE_URL and MATRIX_ACCESS_TOKEN are required")
        self.session = session or requests.Session()
    def parse_event(self, payload: Any, headers=None) -> InboundEvent:
        event = payload.get("event", payload); content = event.get("content", event)
        kind = {"m.image": "image", "m.audio": "audio", "m.video": "video", "m.file": "file"}.get(content.get("msgtype", "m.text"), "text")
        return InboundEvent(platform="matrix", user_id=str(event.get("sender") or payload.get("user_id")), content_type=kind, text=content.get("body"), media_url=content.get("url"))
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        room_id = os.getenv("MATRIX_ROOM_ID")
        if not room_id: raise ValueError("MATRIX_ROOM_ID is required for replies")
        for index, message in enumerate(reply.messages):
            response = self.session.put(f"{self.base_url}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/bot-{index}", headers={"Authorization": f"Bearer {self.access_token}"}, json={"msgtype": "m.text", "body": message.text or message.media_url or ""}, timeout=30)
            response.raise_for_status()
