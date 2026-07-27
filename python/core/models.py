from pydantic import BaseModel, Field
from typing import Literal


ContentType = Literal["text", "image", "audio", "video", "file"]


class InboundEvent(BaseModel):
    platform: str = Field(max_length=32, description="Source integration name")
    user_id: str = Field(max_length=256, description="Platform user ID; internal use only")
    content_type: ContentType
    text: str | None = Field(default=None, max_length=10000)
    media_url: str | None = Field(default=None, max_length=4096)
    reply_token: str | None = Field(default=None, max_length=512)
    reply_to_id: str | None = Field(default=None, max_length=512)
    reply_target: str | None = Field(default=None, max_length=512)
    reply_to_uri: str | None = Field(default=None, max_length=4096)
    reply_to_cid: str | None = Field(default=None, max_length=512)
    reply_mode: str | None = Field(default=None, max_length=32)


class OutboundMessage(BaseModel):
    type: ContentType
    text: str = Field(default="", max_length=10000)
    media_url: str | None = Field(default=None, max_length=4096)


class OutboundReply(BaseModel):
    messages: list[OutboundMessage]


class User(BaseModel):
    id: int
    platform: str = "line"
    platform_user_id: str
    display_name: str | None = None
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""


class Post(BaseModel):
    id: int
    user_id: int
    platform: str = "line"
    type: str
    text: str | None = None
    media_url: str | None = None
    status: str = "published"
    created_at: str = ""
