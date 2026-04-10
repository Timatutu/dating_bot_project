import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LikeCreate(BaseModel):
    to_user_id: uuid.UUID
    action: str = Field(pattern="^(like|skip)$")


class LikeResult(BaseModel):
    action: str
    is_match: bool
    match_id: uuid.UUID | None = None
