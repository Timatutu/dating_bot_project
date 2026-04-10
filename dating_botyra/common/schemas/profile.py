import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=18, le=100)
    gender: str = Field(pattern="^(male|female|other)$")
    bio: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=128)
    lat: float | None = None
    lng: float | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    age: int | None = Field(default=None, ge=18, le=100)
    bio: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=128)
    lat: float | None = None
    lng: float | None = None
    is_visible: bool | None = None


class PhotoOut(BaseModel):
    id: uuid.UUID
    s3_key: str
    is_primary: bool
    position: int

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    age: int
    gender: str
    bio: str | None
    city: str | None
    lat: float | None
    lng: float | None
    photos_count: int
    is_visible: bool
    photos: list[PhotoOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}
