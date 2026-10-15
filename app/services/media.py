from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from fastapi.responses import FileResponse

from app.errors import ResourceNotFound, UnsupportedMediaType, UploadTooLarge
from app.repositories.memory_store import MediaRecord, store
from app.schemas.media import MediaOut

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_UPLOAD_SIZE = 25 * 1024 * 1024
ALLOWED_MEDIA_PREFIXES = ("image/", "audio/", "video/")


def _to_media_out(media: MediaRecord) -> MediaOut:
    return MediaOut(
        id=media.id,
        filename=media.filename,
        content_type=media.content_type,
        url=f"/api/media/{media.id}",
    )


async def upload_media(file: UploadFile) -> MediaOut:
    content_type = file.content_type or ""
    if not content_type.startswith(ALLOWED_MEDIA_PREFIXES):
        raise UnsupportedMediaType(
            "Dozwolone są wyłącznie pliki graficzne, audio i wideo."
        )

    media_id = str(uuid4())
    extension = Path(file.filename or "").suffix[:12]
    destination = UPLOAD_DIR / f"{media_id}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise UploadTooLarge("Maksymalny rozmiar pliku to 25 MB.")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    media = MediaRecord(
        id=media_id,
        filename=Path(file.filename or "plik").name,
        content_type=content_type,
        path=destination,
    )
    store.media_files[media_id] = media
    return _to_media_out(media)


def download_media(media_id: str) -> FileResponse:
    media = store.media_files.get(media_id)
    if media is None or not media.path.is_file():
        raise ResourceNotFound("Nie znaleziono pliku.")
    return FileResponse(
        media.path,
        media_type=media.content_type,
        filename=media.filename,
    )
