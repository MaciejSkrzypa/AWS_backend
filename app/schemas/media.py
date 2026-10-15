from pydantic import BaseModel


class MediaOut(BaseModel):
    id: str
    filename: str
    content_type: str
    url: str
