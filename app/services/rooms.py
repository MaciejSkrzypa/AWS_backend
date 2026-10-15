from datetime import datetime, timezone
from uuid import uuid4

from app.errors import ResourceNotFound
from app.repositories.memory_store import RoomRecord, store
from app.schemas.rooms import RoomCreate, RoomOut


def list_rooms() -> list[RoomOut]:
    rooms = sorted(store.rooms.values(), key=lambda room: room.created_at)
    return [RoomOut.model_validate(room) for room in rooms]


def get_room(room_id: str) -> RoomRecord:
    room = store.rooms.get(room_id)
    if room is None:
        raise ResourceNotFound("Nie znaleziono pokoju.")
    return room


def create_room(data: RoomCreate) -> RoomOut:
    room = RoomRecord(
        id=str(uuid4()),
        name=data.name,
        topic=data.topic,
        created_at=datetime.now(timezone.utc),
    )
    store.rooms[room.id] = room
    store.messages[room.id] = []
    return RoomOut.model_validate(room)
