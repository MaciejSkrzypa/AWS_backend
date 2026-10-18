from datetime import datetime, timezone
from uuid import uuid4

from app.errors import InvalidMessage
from app.repositories.memory_store import MessageRecord, store
from app.schemas.media import MediaOut
from app.schemas.messages import MessageCreate, MessageOut
from app.services.media import get_media_out, verify_media_uploaded
from app.services.rooms import get_room


def _to_message_out(
    message: MessageRecord, media: MediaOut | None = None
) -> MessageOut:
    if media is None and message.media_id:
        media_record = store.media_files.get(message.media_id)
        if media_record:
            media = get_media_out(media_record)
    return MessageOut(
        id=message.id,
        room_id=message.room_id,
        author=message.author,
        text=message.text,
        media=media,
        created_at=message.created_at,
    )


def list_messages(room_id: str) -> list[MessageOut]:
    get_room(room_id)
    return [_to_message_out(item) for item in store.messages[room_id]]


def create_message(room_id: str, data: MessageCreate) -> MessageOut:
    get_room(room_id)
    if not data.text and not data.media_id:
        raise InvalidMessage("Wiadomość nie może być pusta.")
    media = (
        get_media_out(verify_media_uploaded(data.media_id))
        if data.media_id
        else None
    )

    message = MessageRecord(
        id=str(uuid4()),
        room_id=room_id,
        author=data.author,
        text=data.text,
        media_id=data.media_id,
        created_at=datetime.now(timezone.utc),
    )
    store.messages[room_id].append(message)
    return _to_message_out(message, media)
