from .base import PlatformCapabilities


CONTENT_TYPES = ("text", "image", "audio", "video", "file")


def _cap(name: str, *, group: bool = False, attachments: bool = False,
         max_reply_items: int | None = None, webhook: bool = True) -> PlatformCapabilities:
    return PlatformCapabilities(
        name=name,
        receive_types=CONTENT_TYPES,
        send_types=CONTENT_TYPES,
        max_reply_items=max_reply_items,
        supports_group=group,
        supports_multiple_attachments=attachments,
        webhook=webhook,
    )


# These are capability declarations, not claims that credentials or SDKs are configured.
PLATFORM_CATALOG = {
    "line": _cap("line", max_reply_items=5),
    "telegram": _cap("telegram", group=True, max_reply_items=10),
    "discord": _cap("discord", attachments=True, max_reply_items=10),
    "zulip": _cap("zulip", max_reply_items=5),
    "matrix": _cap("matrix", max_reply_items=5),
    "slack": _cap("slack", attachments=True, max_reply_items=5),
    "google_chat": _cap("google_chat", attachments=True, max_reply_items=5),
    "viber": _cap("viber", max_reply_items=5),
    "mastodon": _cap("mastodon", max_reply_items=5),
    "misskey": _cap("misskey", max_reply_items=5),
    "bluesky": _cap("bluesky", max_reply_items=5),
    "whatsapp": _cap("whatsapp", max_reply_items=5),
    "instagram": _cap("instagram", max_reply_items=5),
    "teams": _cap("teams", attachments=True, max_reply_items=5),
    "kakaotalk": _cap("kakaotalk", max_reply_items=5),
    "twitch": _cap("twitch", max_reply_items=5),
    "reddit": _cap("reddit", max_reply_items=5),
}
