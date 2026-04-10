import uuid
from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    telegram_id: int
    username: str | None
    is_active: bool
    sub_expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
