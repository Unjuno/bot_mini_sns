from __future__ import annotations

import os
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class ConfiguredHTTPAdapter(PlatformAdapter):
    """Configurable adapter for platforms whose native transport is not installed.

    It accepts a normalized event or an ``event`` wrapper and posts the common
    reply JSON to a configured endpoint. Native platform adapters can replace
    this class without changing the core service contract.
    """

    def __init__(self, platform: str, endpoint: str | None = None, token: str | None = None,
                 session: requests.Session | None = None):
        if platform not in PLATFORM_CATALOG:
            raise ValueError(f"Unknown platform: {platform}")
        self.capabilities = PLATFORM_CATALOG[platform]
        self.endpoint = endpoint or os.getenv(f"{platform.upper()}_ADAPTER_ENDPOINT")
        self.token = token or os.getenv(f"{platform.upper()}_TOKEN")
        if not self.endpoint:
            raise ValueError(f"{platform.upper()}_ADAPTER_ENDPOINT is required")
        self.session = session or requests.Session()

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        value = payload.get("event", payload)
        event = InboundEvent.model_validate(value)
        if event.platform != self.capabilities.name:
            raise ValueError("Event platform does not match adapter")
        return event

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.session.post(
            self.endpoint,
            headers=headers,
            json={"event": event.model_dump(), "reply": reply.model_dump()},
            timeout=30,
        )
        response.raise_for_status()
