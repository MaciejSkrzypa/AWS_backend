from fastapi import APIRouter, status

from app.schemas.media import MediaUploadOut, MediaUploadRequest
from app.services.media import create_media_upload

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload-url", response_model=MediaUploadOut, status_code=status.HTTP_201_CREATED)
def post_media_upload_url(data: MediaUploadRequest) -> MediaUploadOut:
    return create_media_upload(data)
