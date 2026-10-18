from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class RoomRecord:
    id: str
    name: str
    topic: str
    created_at: datetime


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


@dataclass
class MemoryStore:
    rooms: dict[str, RoomRecord] = field(default_factory=dict)
    messages: dict[str, list[MessageRecord]] = field(default_factory=dict)
    media_files: dict[str, MediaRecord] = field(default_factory=dict)


def _seed_store() -> MemoryStore:
    now = datetime.now(timezone.utc)
    room_records = [
        RoomRecord("general", "General", "Wszystko, co warto omówić", now),
        RoomRecord(
            "inspiration",
            "Inspiracje",
            "Pomysły, linki i rzeczy, które nas napędzają",
            now,
        ),
    ]
    store = MemoryStore(
        rooms={room.id: room for room in room_records},
        messages={room.id: [] for room in room_records},
    )
    store.messages["general"] = [
        MessageRecord(
            str(uuid4()),
            "general",
            "Maja",
            "Cześć wszystkim! Miło widzieć nas w jednym miejscu 👋",
            None,
            now,
        ),
        MessageRecord(
            str(uuid4()),
            "general",
            "Kuba",
            "Wygląda świetnie. Możemy tu wrzucać też pliki i zdjęcia.",
            None,
            now,
        ),
    ]
    return store


store = _seed_store()
