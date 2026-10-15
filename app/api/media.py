from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.schemas.media import MediaOut
from app.services.media import download_media, upload_media

router = APIRouter(prefix="/media", tags=["media"])


@router.post("", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def post_media(file: UploadFile = File(...)) -> MediaOut:
    return await upload_media(file)


@router.get("/{media_id}")
def get_media(media_id: str) -> FileResponse:
    return download_media(media_id)
