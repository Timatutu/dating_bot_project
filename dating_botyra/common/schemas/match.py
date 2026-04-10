import uuid
from datetime import datetime

from pydantic import BaseModel


class MatchOut(BaseModel):
    id: uuid.UUID
    user1_id: uuid.UUID
    user2_id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
