from __future__ import annotations

from typing import Any

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class MockPlatformAdapter(PlatformAdapter):
    """Offline adapter used to verify every platform contract without credentials."""

    def __init__(self, platform: str):
        if platform not in PLATFORM_CATALOG:
            raise ValueError(f"Unknown platform: {platform}")
        self.capabilities = PLATFORM_CATALOG[platform]
        self.sent_replies: list[OutboundReply] = []

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        event = InboundEvent.model_validate(payload)
        if event.platform != self.capabilities.name:
            raise ValueError("Event platform does not match adapter")
        if event.content_type not in self.capabilities.receive_types:
            raise ValueError("Content type is not supported by this adapter")
        return event

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        if len(reply.messages) > (self.capabilities.max_reply_items or len(reply.messages)):
            raise ValueError("Reply exceeds platform capacity")
        if any(message.type not in self.capabilities.send_types for message in reply.messages):
            raise ValueError("Reply contains an unsupported content type")
        self.sent_replies.append(reply)
