from enum import Enum, auto

from .models import ContentType, InboundEvent, OutboundMessage, OutboundReply


class ActionType(Enum):
    SAVE_TEXT = auto()
    SAVE_MEDIA = auto()
    SHOW_USAGE = auto()
    REPLY_RECENT_POSTS = auto()


class Action:
    def __init__(
        self,
        type: ActionType,
        text: str | None = None,
        media_url: str | None = None,
        content_type: str | None = None,
    ):
        self.type = type
        self.text = text
        self.media_url = media_url
        self.content_type = content_type


CONTENT_TYPE_LABELS: dict[str, str] = {
    "text": "文章",
    "image": "写真",
    "audio": "音声",
    "video": "動画",
    "file": "ファイル",
}


def decide_actions(is_first_post: bool, event: InboundEvent) -> list[Action]:
    actions: list[Action] = []
    if event.content_type == "text":
        actions.append(Action(ActionType.SAVE_TEXT, text=event.text))
    else:
        actions.append(
            Action(
                ActionType.SAVE_MEDIA,
                text=event.text,
                media_url=event.media_url,
                content_type=event.content_type,
            )
        )
    if is_first_post:
        actions.append(Action(ActionType.SHOW_USAGE))
    else:
        actions.append(Action(ActionType.REPLY_RECENT_POSTS))
    return actions


def format_usage_text() -> str:
    return (
        "使い方:\n"
        "・文章、写真、音声、動画、ファイルを送ると投稿として保存されます。\n"
        "・保存後、最近の投稿が返信されます。"
    )


def format_recent_posts_text(posts: list[dict]) -> str:
    lines = ["保存済みの投稿:"]
    for post in posts:
        ptype = post.get("type", "")
        value = (post.get("text") or "").replace("\n", " ").strip()
        label = CONTENT_TYPE_LABELS.get(ptype, ptype)
        line = f"・{label}"
        if value:
            line += f": {value[:80]}"
        lines.append(line)
    return "\n".join(lines) if lines else "保存済みの投稿はありません。"


def build_reply(actions: list[Action], recent_posts: list[dict] | None = None) -> OutboundReply:
    messages: list[OutboundMessage] = []
    has_usage = any(a.type == ActionType.SHOW_USAGE for a in actions)
    has_recent = any(a.type == ActionType.REPLY_RECENT_POSTS for a in actions)
    if has_usage:
        messages.append(OutboundMessage(type="text", text=format_usage_text()))
    elif has_recent:
        text = "投稿しました。\n\n"
        text += format_recent_posts_text(recent_posts or [])
        messages.append(OutboundMessage(type="text", text=text))
    return OutboundReply(messages=messages)
