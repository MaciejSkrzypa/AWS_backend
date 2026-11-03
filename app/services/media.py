import os
from pathlib import PurePosixPath
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.errors import ResourceNotFound, UnsupportedMediaType
from app.repositories.dynamodb import (
    get_media as find_media,
    list_messages as find_messages,
    save_media,
)
from app.repositories.records import MediaRecord
from app.schemas.media import MediaOut, MediaUploadOut, MediaUploadRequest
from app.services.rooms import get_room

MAX_UPLOAD_SIZE = 25 * 1024 * 1024
PRESIGNED_URL_TTL = 900
ALLOWED_MEDIA_PREFIXES = ("image/", "audio/", "video/")


def _s3_client():
    bucket = os.getenv("S3_MEDIA_BUCKET", "")
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if not bucket or not region:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Magazyn multimediów S3 nie jest skonfigurowany.",
        )
    return boto3.client("s3", region_name=region), bucket


def _safe_filename(filename: str) -> str:
    return PurePosixPath(filename.replace("\\", "/")).name


def get_media_out(media: MediaRecord) -> MediaOut:
    client, bucket = _s3_client()
    if media.content_type.startswith("image/"):
        thumbnail_url = None
        if media.thumbnail_status == "ready" and media.thumbnail_object_key:
            try:
                thumbnail_url = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": media.thumbnail_object_key},
                    ExpiresIn=PRESIGNED_URL_TTL,
                )
            except (BotoCoreError, ClientError) as error:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Nie udało się przygotować pobierania miniatury z S3.",
                ) from error
        return MediaOut(
            id=media.id,
            filename=media.filename,
            content_type=media.content_type,
            url=None,
            thumbnail_url=thumbnail_url,
            thumbnail_status=media.thumbnail_status,
        )

    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": media.object_key},
            ExpiresIn=PRESIGNED_URL_TTL,
        )
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie udało się przygotować pobierania z S3.",
        ) from error
    return MediaOut(
        id=media.id,
        filename=media.filename,
        content_type=media.content_type,
        url=url,
        thumbnail_status="not_applicable",
    )


def create_media_upload(data: MediaUploadRequest) -> MediaUploadOut:
    content_type = data.content_type
    if not content_type.startswith(ALLOWED_MEDIA_PREFIXES):
        raise UnsupportedMediaType(
            "Dozwolone są wyłącznie pliki graficzne, audio i wideo."
        )

    media_id = str(uuid4())
    object_key = f"media/{media_id}"
    media = MediaRecord(
        id=media_id,
        filename=_safe_filename(data.filename) or "plik",
        content_type=content_type,
        object_key=object_key,
        thumbnail_status=(
            "pending" if content_type.startswith("image/") else "not_applicable"
        ),
    )

    client, bucket = _s3_client()
    try:
        presigned_post = client.generate_presigned_post(
            Bucket=bucket,
            Key=object_key,
            Fields={"Content-Type": content_type},
            Conditions=[
                ["content-length-range", 1, MAX_UPLOAD_SIZE],
                ["eq", "$Content-Type", content_type],
            ],
            ExpiresIn=PRESIGNED_URL_TTL,
        )
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie udało się przygotować przesyłania do S3.",
        ) from error

    save_media(media)
    return MediaUploadOut(
        id=media.id,
        filename=media.filename,
        content_type=media.content_type,
        upload_url=presigned_post["url"],
        fields=presigned_post["fields"],
    )


def verify_media_uploaded(media_id: str) -> MediaRecord:
    media = find_media(media_id)
    if media is None:
        raise ResourceNotFound("Nie znaleziono pliku.")

    client, bucket = _s3_client()
    try:
        stored = client.head_object(Bucket=bucket, Key=media.object_key)
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise ResourceNotFound("Załącznik nie został przesłany do S3.") from error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie można zweryfikować przesłanego załącznika w S3.",
        ) from error
    except BotoCoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie można połączyć się z S3.",
        ) from error

    if stored.get("ContentLength", 0) > MAX_UPLOAD_SIZE:
        raise UnsupportedMediaType("Maksymalny rozmiar pliku to 25 MB.")
    if stored.get("ContentType") != media.content_type:
        raise UnsupportedMediaType("Typ przesłanego pliku jest nieprawidłowy.")
    return media


def get_original_media_url(media_id: str, room_id: str, member_id: str) -> str:
    get_room(room_id, member_id)
    if not any(
        message.media_id == media_id for message in find_messages(room_id)
    ):
        raise ResourceNotFound("Nie znaleziono załącznika w tym pokoju.")

    media = find_media(media_id)
    if media is None:
        raise ResourceNotFound("Nie znaleziono pliku.")

    client, bucket = _s3_client()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": media.object_key},
            ExpiresIn=PRESIGNED_URL_TTL,
        )
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie udało się przygotować pobierania z S3.",
        ) from error
