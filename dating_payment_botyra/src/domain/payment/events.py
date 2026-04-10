import uuid
from dataclasses import dataclass

from src.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class PaymentCreated(DomainEvent):
    payment_id: uuid.UUID = None
    user_id: uuid.UUID = None
    provider: str = ""


@dataclass(frozen=True)
class PaymentSucceeded(DomainEvent):
    payment_id: uuid.UUID = None
    user_id: uuid.UUID = None
    subscription_id: uuid.UUID = None


@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    payment_id: uuid.UUID = None
    user_id: uuid.UUID = None
