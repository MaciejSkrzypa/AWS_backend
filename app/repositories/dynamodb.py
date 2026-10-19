import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.repositories.records import MediaRecord, MessageRecord, RoomRecord


def _table(environment_variable: str):
    table_name = os.getenv(environment_variable, "").strip()
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if not table_name or not region:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Baza DynamoDB nie jest skonfigurowana.",
        )
    return boto3.resource("dynamodb", region_name=region).Table(table_name)


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Nie można połączyć się z bazą DynamoDB.",
    )


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def list_rooms(member_id: str) -> list[RoomRecord]:
    table = _table("DYNAMODB_ROOMS_TABLE")
    rooms: list[RoomRecord] = []
    try:
        response = table.scan(
            FilterExpression=Attr("member_ids").contains(member_id)
        )
        while True:
            rooms.extend(
                RoomRecord(
                    id=item["id"],
                    code=item["code"],
                    name=item["name"],
                    topic=item["topic"],
                    created_at=_datetime(item["created_at"]),
                    member_ids=set(item.get("member_ids", set())),
                )
                for item in response.get("Items", [])
            )
            last_key = response.get("LastEvaluatedKey")
            if last_key is None:
                return rooms
            response = table.scan(
                FilterExpression=Attr("member_ids").contains(member_id),
                ExclusiveStartKey=last_key,
            )
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error


def get_room(room_id: str) -> RoomRecord | None:
    table = _table("DYNAMODB_ROOMS_TABLE")
    try:
        item = table.get_item(Key={"id": room_id}).get("Item")
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error
    if item is None:
        return None
    return RoomRecord(
        id=item["id"],
        code=item["code"],
        name=item["name"],
        topic=item["topic"],
        created_at=_datetime(item["created_at"]),
        member_ids=set(item.get("member_ids", set())),
    )


def create_room(room: RoomRecord) -> bool:
    table = _table("DYNAMODB_ROOMS_TABLE")
    try:
        table.put_item(
            Item={
                "id": room.id,
                "code": room.code,
                "name": room.name,
                "topic": room.topic,
                "created_at": room.created_at.isoformat(),
                "member_ids": room.member_ids,
            },
            ConditionExpression="attribute_not_exists(id)",
        )
    except ClientError as error:
        if (
            error.response.get("Error", {}).get("Code")
            == "ConditionalCheckFailedException"
        ):
            return False
        raise _database_unavailable() from error
    except BotoCoreError as error:
        raise _database_unavailable() from error
    return True


def add_room_member(room_id: str, member_id: str) -> None:
    table = _table("DYNAMODB_ROOMS_TABLE")
    try:
        table.update_item(
            Key={"id": room_id},
            UpdateExpression="ADD member_ids :member_ids",
            ExpressionAttributeValues={":member_ids": {member_id}},
            ConditionExpression="attribute_exists(id)",
        )
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error


def list_messages(room_id: str) -> list[MessageRecord]:
    table = _table("DYNAMODB_MESSAGES_TABLE")
    messages: list[MessageRecord] = []
    try:
        response = table.query(
            KeyConditionExpression=Key("room_id").eq(room_id),
            ScanIndexForward=True,
            ConsistentRead=True,
        )
        while True:
            messages.extend(
                MessageRecord(
                    id=item["id"],
                    room_id=item["room_id"],
                    author=item["author"],
                    text=item["text"],
                    media_id=item.get("media_id"),
                    created_at=_datetime(item["created_at"]),
                )
                for item in response.get("Items", [])
            )
            last_key = response.get("LastEvaluatedKey")
            if last_key is None:
                return messages
            response = table.query(
                KeyConditionExpression=Key("room_id").eq(room_id),
                ScanIndexForward=True,
                ConsistentRead=True,
                ExclusiveStartKey=last_key,
            )
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error


def create_message(message: MessageRecord) -> None:
    table = _table("DYNAMODB_MESSAGES_TABLE")
    item = {
        "room_id": message.room_id,
        "message_key": f"{message.created_at.isoformat()}#{message.id}",
        "id": message.id,
        "author": message.author,
        "text": message.text,
        "created_at": message.created_at.isoformat(),
    }
    if message.media_id:
        item["media_id"] = message.media_id
    try:
        table.put_item(Item=item)
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error


def get_media(media_id: str) -> MediaRecord | None:
    table = _table("DYNAMODB_MEDIA_TABLE")
    try:
        item = table.get_item(Key={"id": media_id}).get("Item")
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error
    if item is None:
        return None
    return MediaRecord(
        id=item["id"],
        filename=item["filename"],
        content_type=item["content_type"],
        object_key=item["object_key"],
    )


def save_media(media: MediaRecord) -> None:
    table = _table("DYNAMODB_MEDIA_TABLE")
    try:
        table.put_item(
            Item={
                "id": media.id,
                "filename": media.filename,
                "content_type": media.content_type,
                "object_key": media.object_key,
            }
        )
    except (BotoCoreError, ClientError) as error:
        raise _database_unavailable() from error
