import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SubscriptionView:
    subscription_id: uuid.UUID
    plan: str
    status: str
    expires_at: datetime | None
    is_active: bool
