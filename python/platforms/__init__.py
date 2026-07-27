"""Platform adapter contracts and catalog for the multi-platform implementation."""

from .base import PlatformAdapter, PlatformCapabilities
from .catalog import PLATFORM_CATALOG
from .mock import MockPlatformAdapter
from .telegram import TelegramAdapter

__all__ = ["PlatformAdapter", "PlatformCapabilities", "PLATFORM_CATALOG", "MockPlatformAdapter", "TelegramAdapter"]
