from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Nazwa pokoju nie może być pusta.")
        return name


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: datetime
    member_count: int


class RoomJoin(BaseModel):
    id: str = Field(pattern=r"^[A-HJ-NP-Z2-9]{10}$")

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Identyfikator pokoju musi być tekstem.")
        return value.strip().replace("-", "").replace(" ", "").upper()
