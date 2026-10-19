from datetime import datetime, timezone
import secrets

from app.errors import ResourceNotFound
from app.repositories.dynamodb import add_room_member
from app.repositories.dynamodb import create_room as save_room
from app.repositories.dynamodb import get_room as find_room
from app.repositories.dynamodb import list_rooms as find_rooms
from app.repositories.records import RoomRecord
from app.schemas.rooms import RoomCreate, RoomJoin, RoomOut

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def list_rooms(member_id: str) -> list[RoomOut]:
    rooms = sorted(find_rooms(member_id), key=lambda room: room.created_at)
    return [RoomOut.model_validate(room) for room in rooms]


def get_room(room_id: str, member_id: str) -> RoomRecord:
    room = find_room(room_id)
    if room is None or member_id not in room.member_ids:
        raise ResourceNotFound("Nie znaleziono pokoju.")
    return room


def join_room(data: RoomJoin, member_id: str) -> RoomOut:
    room = find_room(data.code)
    if room is None:
        raise ResourceNotFound("Nie znaleziono pokoju o podanym kodzie.")
    add_room_member(room.id, member_id)
    return RoomOut.model_validate(room)


def create_room(data: RoomCreate, member_id: str) -> RoomOut:
    while True:
        code = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(10))
        room = RoomRecord(
            id=code,
            code=code,
            name=data.name,
            topic=data.topic,
            created_at=datetime.now(timezone.utc),
            member_ids={member_id},
        )
        if save_room(room):
            return RoomOut.model_validate(room)
