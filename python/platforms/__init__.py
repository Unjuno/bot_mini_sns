"""Platform adapter contracts and catalog for the multi-platform implementation."""

from .base import PlatformAdapter, PlatformCapabilities
from .catalog import PLATFORM_CATALOG
from .mock import MockPlatformAdapter
from .telegram import TelegramAdapter
from .discord import DiscordAdapter
from .misskey import MisskeyAdapter
from .mastodon import MastodonAdapter
from .bluesky import BlueskyAdapter
from .configured import ConfiguredHTTPAdapter
from .zulip import ZulipAdapter
from .matrix import MatrixAdapter
from .slack import SlackAdapter
from .google_chat import GoogleChatAdapter
from .registry import create_adapter

__all__ = ["PlatformAdapter", "PlatformCapabilities", "PLATFORM_CATALOG", "MockPlatformAdapter", "TelegramAdapter", "DiscordAdapter", "MisskeyAdapter", "MastodonAdapter", "BlueskyAdapter", "ZulipAdapter", "MatrixAdapter", "SlackAdapter", "GoogleChatAdapter", "ConfiguredHTTPAdapter", "create_adapter"]
