from __future__ import annotations

from .base import PlatformAdapter
from .discord import DiscordAdapter
from .mock import MockPlatformAdapter
from .misskey import MisskeyAdapter
from .mastodon import MastodonAdapter
from .bluesky import BlueskyAdapter
from .configured import ConfiguredHTTPAdapter
from .telegram import TelegramAdapter
from .zulip import ZulipAdapter
from .matrix import MatrixAdapter
from .slack import SlackAdapter
from .google_chat import GoogleChatAdapter
from .viber import ViberAdapter
from .whatsapp import WhatsAppAdapter
from .instagram import InstagramAdapter
from .teams import TeamsAdapter
from .twitch import TwitchAdapter
from .reddit import RedditAdapter
from .kakaotalk import KakaoTalkAdapter


LIVE_ADAPTERS = {
    "line": None,  # LINE remains hosted by the existing Flask app during migration.
    "telegram": TelegramAdapter,
    "discord": DiscordAdapter,
    "misskey": MisskeyAdapter,
    "mastodon": MastodonAdapter,
    "bluesky": BlueskyAdapter,
    "zulip": ZulipAdapter,
    "matrix": MatrixAdapter,
    "slack": SlackAdapter,
    "google_chat": GoogleChatAdapter,
    "viber": ViberAdapter,
    "whatsapp": WhatsAppAdapter,
    "instagram": InstagramAdapter,
    "teams": TeamsAdapter,
    "twitch": TwitchAdapter,
    "reddit": RedditAdapter,
    "kakaotalk": KakaoTalkAdapter,
}

CONFIGURED_PLATFORMS = {
}


def create_adapter(platform: str, *, offline: bool = False, **kwargs) -> PlatformAdapter:
    """Create a live adapter or an offline contract adapter for any catalog entry."""
    if offline:
        return MockPlatformAdapter(platform)
    if platform in CONFIGURED_PLATFORMS:
        return ConfiguredHTTPAdapter(platform, **kwargs)
    adapter_type = LIVE_ADAPTERS.get(platform)
    if adapter_type is None:
        if platform == "line":
            raise NotImplementedError("LINE uses the existing Flask app entrypoint")
        raise NotImplementedError(f"Live adapter is not implemented: {platform}")
    return adapter_type(**kwargs)
