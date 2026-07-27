from __future__ import annotations

import os
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class DiscordAdapter(PlatformAdapter):
    """Discord Gateway-event parser and REST message sender."""

    capabilities = PLATFORM_CATALOG["discord"]

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN is required")
        self.session = session or requests.Session()
        self.base_url = "https://discord.com/api/v10"

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        if payload.get("t") not in (None, "MESSAGE_CREATE"):
            raise ValueError("Discord payload is not a message event")
        message = payload.get("d", payload)
        if not message.get("channel_id") or not message.get("author", {}).get("id"):
            raise ValueError("Discord message has no channel or author")
        common = {"platform": "discord", "user_id": str(message["channel_id"])}
        if message.get("content"):
            return InboundEvent(**common, content_type="text", text=message["content"])
        attachments = message.get("attachments") or []
        if not attachments:
            raise ValueError("Discord message has no supported content")
        attachment = attachments[0]
        content_type = self._content_type(attachment.get("content_type", ""), attachment.get("filename", ""))
        return InboundEvent(**common, content_type=content_type, media_url=attachment.get("url"))

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        url = f"{self.base_url}/channels/{event.user_id}/messages"
        headers = {"Authorization": f"Bot {self.token}"}
        messages = reply.messages[: self.capabilities.max_reply_items or len(reply.messages)]
        body: dict[str, Any] = {"allowed_mentions": {"parse": []}}
        if all(message.type == "text" for message in messages):
            body["content"] = "\n\n".join(message.text for message in messages)[:2000]
        else:
            body["content"] = ""
            body["embeds"] = [
                {"image": {"url": message.media_url}}
                if message.type == "image" and message.media_url
                else {"description": message.media_url or message.text}
                for message in messages
            ][:10]
        response = self.session.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()

    @staticmethod
    def _content_type(content_type: str, filename: str) -> str:
        value = f"{content_type} {filename}".lower()
        if value.startswith("image/") or any(ext in value for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
            return "image"
        if value.startswith("audio/") or any(ext in value for ext in (".mp3", ".m4a", ".wav", ".ogg")):
            return "audio"
        if value.startswith("video/") or any(ext in value for ext in (".mp4", ".mov", ".webm")):
            return "video"
        return "file"
