from datetime import datetime, timezone
from uuid import uuid4

from app.errors import InvalidMessage, ResourceNotFound
from app.repositories.memory_store import MessageRecord, store
from app.schemas.media import MediaOut
from app.schemas.messages import MessageCreate, MessageOut
from app.services.rooms import get_room


def _to_message_out(message: MessageRecord) -> MessageOut:
    media_record = store.media_files.get(message.media_id) if message.media_id else None
    media = (
        MediaOut(
            id=media_record.id,
            filename=media_record.filename,
            content_type=media_record.content_type,
            url=f"/api/media/{media_record.id}",
        )
        if media_record
        else None
    )
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
    if data.media_id and data.media_id not in store.media_files:
        raise ResourceNotFound("Nie znaleziono załącznika.")

    message = MessageRecord(
        id=str(uuid4()),
        room_id=room_id,
        author=data.author,
        text=data.text,
        media_id=data.media_id,
        created_at=datetime.now(timezone.utc),
    )
    store.messages[room_id].append(message)
    return _to_message_out(message)
