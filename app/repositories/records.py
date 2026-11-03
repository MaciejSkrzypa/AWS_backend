from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RoomRecord:
    id: str
    name: str
    created_at: datetime
    member_ids: set[str] = field(default_factory=set)

    @property
    def member_count(self) -> int:
        return len(self.member_ids)


@dataclass
class MessageRecord:
    id: str
    room_id: str
    author_id: str | None
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
    thumbnail_status: str = "not_applicable"
    thumbnail_object_key: str | None = None
