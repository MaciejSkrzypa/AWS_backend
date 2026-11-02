from typing import Any

from fastapi import APIRouter, Depends, status

from app.auth import (
    CognitoUserProfile,
    get_cognito_user_profile,
    require_cognito_access_token,
)
from app.schemas.messages import MessageCreate, MessageOut
from app.services.messages import create_message, list_messages

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageOut])
def get_messages(
    room_id: str,
    identity: dict[str, Any] = Depends(require_cognito_access_token),
) -> list[MessageOut]:
    return list_messages(room_id, identity["sub"])


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def post_message(
    room_id: str,
    message: MessageCreate,
    user: CognitoUserProfile = Depends(get_cognito_user_profile),
) -> MessageOut:
    authenticated_message = message.model_copy(update={"author": user.nickname})
    return create_message(room_id, authenticated_message, user.sub)
