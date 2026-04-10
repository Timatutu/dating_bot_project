import uuid
from dataclasses import dataclass

from src.domain.payment.value_objects import Provider
from src.domain.subscription.value_objects import Plan


@dataclass(frozen=True)
class CreatePaymentCommand:
    user_id: uuid.UUID
    plan: Plan
    provider: Provider


@dataclass(frozen=True)
class ConfirmPaymentCommand:
    payment_id: uuid.UUID
    provider_payment_id: str


@dataclass(frozen=True)
class CreateCryptoPaymentCommand:
    user_id: uuid.UUID
    plan: Plan
    provider: Provider  


@dataclass(frozen=True)
class CheckCryptoPaymentCommand:
    payment_id: uuid.UUID
