from typing import Any

from fastapi import APIRouter, Depends, status

from app.auth import require_cognito_access_token
from app.schemas.rooms import RoomCreate, RoomJoin, RoomOut
from app.services.rooms import create_room, join_room, list_rooms

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def get_rooms(
    identity: dict[str, Any] = Depends(require_cognito_access_token),
) -> list[RoomOut]:
    return list_rooms(identity["sub"])


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def post_room(
    room: RoomCreate,
    identity: dict[str, Any] = Depends(require_cognito_access_token),
) -> RoomOut:
    return create_room(room, identity["sub"])


@router.post("/join", response_model=RoomOut)
def post_join_room(
    data: RoomJoin,
    identity: dict[str, Any] = Depends(require_cognito_access_token),
) -> RoomOut:
    return join_room(data, identity["sub"])
