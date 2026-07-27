from __future__ import annotations

import os
from typing import Any

import requests

from core.models import InboundEvent, OutboundReply
from .base import PlatformAdapter
from .catalog import PLATFORM_CATALOG


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API adapter using the official HTTPS API."""

    capabilities = PLATFORM_CATALOG["telegram"]

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.session = session or requests.Session()
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def parse_event(self, payload: Any, headers: dict[str, str] | None = None) -> InboundEvent:
        message = payload.get("message") or payload.get("edited_message")
        if not message or not message.get("from"):
            raise ValueError("Telegram update has no supported message")
        user_id = str(message["chat"]["id"])
        common = {"platform": "telegram", "user_id": user_id}
        if message.get("text") is not None:
            return InboundEvent(**common, content_type="text", text=message["text"])
        if message.get("photo"):
            return InboundEvent(**common, content_type="image", media_url=f"telegram:{message['photo'][-1]['file_id']}")
        for content_type, key in (("audio", "audio"), ("video", "video"), ("file", "document")):
            if message.get(key):
                return InboundEvent(**common, content_type=content_type, media_url=f"telegram:{message[key]['file_id']}")
        raise ValueError("Telegram content type is not supported")

    def send_reply(self, event: InboundEvent, reply: OutboundReply) -> None:
        for message in reply.messages[: self.capabilities.max_reply_items or len(reply.messages)]:
            method, field, value = self._message_request(message.type, message.media_url, message.text)
            response = self.session.post(
                f"{self.base_url}/{method}",
                json={"chat_id": event.user_id, field: value, **({"caption": message.text} if message.text and field != "text" else {})},
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(f"Telegram API error: {body}")

    @staticmethod
    def _message_request(content_type: str, media_url: str | None, text: str):
        if content_type == "text":
            return "sendMessage", "text", text
        if not media_url:
            raise ValueError("Telegram media reply requires media_url")
        value = media_url.removeprefix("telegram:")
        method_by_type = {"image": "sendPhoto", "audio": "sendAudio", "video": "sendVideo", "file": "sendDocument"}
        if content_type not in method_by_type:
            raise ValueError(f"Unsupported Telegram content type: {content_type}")
        field_by_type = {"image": "photo", "audio": "audio", "video": "video", "file": "document"}
        return method_by_type[content_type], field_by_type[content_type], value
