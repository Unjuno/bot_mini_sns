from __future__ import annotations

from .base import PlatformAdapter
from .discord import DiscordAdapter
from .mock import MockPlatformAdapter
from .telegram import TelegramAdapter


LIVE_ADAPTERS = {
    "line": None,  # LINE remains hosted by the existing Flask app during migration.
    "telegram": TelegramAdapter,
    "discord": DiscordAdapter,
}


def create_adapter(platform: str, *, offline: bool = False, **kwargs) -> PlatformAdapter:
    """Create a live adapter or an offline contract adapter for any catalog entry."""
    if offline:
        return MockPlatformAdapter(platform)
    adapter_type = LIVE_ADAPTERS.get(platform)
    if adapter_type is None:
        if platform == "line":
            raise NotImplementedError("LINE uses the existing Flask app entrypoint")
        raise NotImplementedError(f"Live adapter is not implemented: {platform}")
    return adapter_type(**kwargs)
