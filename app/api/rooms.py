from fastapi import APIRouter, status

from app.schemas.rooms import RoomCreate, RoomOut
from app.services.rooms import create_room, list_rooms

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def get_rooms() -> list[RoomOut]:
    return list_rooms()


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def post_room(room: RoomCreate) -> RoomOut:
    return create_room(room)
