from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.media import MediaOut


class MessageCreate(BaseModel):
    author: str = Field(default="Gość", min_length=1, max_length=40)
    text: str = Field(default="", max_length=2000)
    media_id: str | None = None

    @field_validator("author")
    @classmethod
    def trim_author(cls, value: str) -> str:
        return value.strip() or "Gość"

    @field_validator("text")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class MessageOut(BaseModel):
    id: str
    room_id: str
    author: str
    text: str
    media: MediaOut | None
    created_at: datetime
