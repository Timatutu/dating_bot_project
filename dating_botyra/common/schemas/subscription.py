import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubscriptionCreate(BaseModel):
    plan: str = Field(pattern="^(monthly|yearly)$")
    provider: str = Field(pattern="^(yookassa|tg_stars|crypto)$")


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan: str
    status: str
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    amount: int
    provider: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
