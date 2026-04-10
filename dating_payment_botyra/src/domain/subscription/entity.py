import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from src.domain.shared.entity import Entity
from src.domain.subscription.value_objects import PLAN_DAYS, Plan, SubscriptionStatus


@dataclass
class Subscription(Entity):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    plan: Plan = Plan.MONTH
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def activate(self) -> None:
        days = PLAN_DAYS[self.plan]
        now = datetime.now(timezone.utc)
        if self.expires_at and self.expires_at.tzinfo is None:
            self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        base = self.expires_at if (self.expires_at and self.expires_at > now) else now
        self.expires_at = base + timedelta(days=days)
        self.status = SubscriptionStatus.ACTIVE

    def expire(self) -> None:
        self.status = SubscriptionStatus.EXPIRED

    @property
    def is_active(self) -> bool:
        if self.status != SubscriptionStatus.ACTIVE or self.expires_at is None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > datetime.now(timezone.utc)
