import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.payment.value_objects import Money, PaymentStatus, Provider
from src.domain.shared.entity import Entity


@dataclass
class Payment(Entity):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    subscription_id: uuid.UUID | None = None
    provider: Provider = Provider.TG_STARS
    amount: Money = field(default_factory=lambda: Money(amount=1, currency="XTR"))
    status: PaymentStatus = PaymentStatus.PENDING
    provider_payment_id: str | None = None
    deposit_address: str | None = None       
    expires_at: datetime | None = None       
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def succeed(self, provider_payment_id: str) -> None:
        self.status = PaymentStatus.SUCCEEDED
        self.provider_payment_id = provider_payment_id

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return lambda: datetime.now(timezone.utc)() > self.expires_at
