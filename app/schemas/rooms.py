from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    topic: str = Field(default="", max_length=120)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Nazwa pokoju nie może być pusta.")
        return name

    @field_validator("topic")
    @classmethod
    def trim_topic(cls, value: str) -> str:
        return value.strip()


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    topic: str
    created_at: datetime


class RoomJoin(BaseModel):
    code: str = Field(pattern=r"^[A-HJ-NP-Z2-9]{10}$")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Kod pokoju musi być tekstem.")
        return value.strip().replace("-", "").replace(" ", "").upper()
