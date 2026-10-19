from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RoomRecord:
    id: str
    code: str
    name: str
    topic: str
    created_at: datetime
    member_ids: set[str] = field(default_factory=set)


@dataclass
class MessageRecord:
    id: str
    room_id: str
    author: str
    text: str
    media_id: str | None
    created_at: datetime


@dataclass
class MediaRecord:
    id: str
    filename: str
    content_type: str
    object_key: str
