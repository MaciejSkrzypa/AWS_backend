from pydantic import BaseModel, Field


class MediaUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)


class MediaUploadOut(BaseModel):
    id: str
    filename: str
    content_type: str
    upload_url: str
    fields: dict[str, str]


class MediaOut(BaseModel):
    id: str
    filename: str
    content_type: str
    url: str
