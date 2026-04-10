import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class SubscriptionActivated(DomainEvent):
    subscription_id: uuid.UUID = None
    user_id: uuid.UUID = None
    expires_at: datetime = None


@dataclass(frozen=True)
class SubscriptionExpired(DomainEvent):
    subscription_id: uuid.UUID = None
    user_id: uuid.UUID = None
