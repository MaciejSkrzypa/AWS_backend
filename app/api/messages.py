from typing import Any

from fastapi import APIRouter, Depends, status

from app.auth import require_cognito_access_token
from app.schemas.messages import MessageCreate, MessageOut
from app.services.messages import create_message, list_messages

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageOut])
def get_messages(room_id: str) -> list[MessageOut]:
    return list_messages(room_id)


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def post_message(
    room_id: str,
    message: MessageCreate,
    identity: dict[str, Any] = Depends(require_cognito_access_token),
) -> MessageOut:
    author = identity.get("username") or identity["sub"]
    authenticated_message = message.model_copy(update={"author": author})
    return create_message(room_id, authenticated_message)
