from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from core.models import InboundEvent, OutboundReply


@dataclass(frozen=True)
class PlatformCapabilities:
    """What an adapter can receive and send without platform-specific guessing."""

    name: str
    receive_types: tuple[str, ...]
    send_types: tuple[str, ...]
    max_reply_items: int | None
    supports_group: bool
    supports_multiple_attachments: bool
    webhook: bool


class PlatformAdapter(ABC):
    """Boundary between a platform API and the platform-independent core."""

    capabilities: PlatformCapabilities

    @abstractmethod
    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        """Convert a platform event into the common inbound event."""

    @abstractmethod
    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        """Render and send a common reply using the platform API."""
