from pydantic import BaseModel, Field
from typing import Literal


ContentType = Literal["text", "image", "audio", "video", "file"]


class InboundEvent(BaseModel):
    platform: str = Field(description="Source integration name")
    user_id: str = Field(description="Platform user ID; internal use only")
    content_type: ContentType
    text: str | None = None
    media_url: str | None = None


class OutboundMessage(BaseModel):
    type: ContentType
    text: str = ""
    media_url: str | None = None


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
