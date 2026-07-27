"""Platform adapter contracts and catalog for the multi-platform implementation."""

from .base import PlatformAdapter, PlatformCapabilities
from .catalog import PLATFORM_CATALOG

__all__ = ["PlatformAdapter", "PlatformCapabilities", "PLATFORM_CATALOG"]
