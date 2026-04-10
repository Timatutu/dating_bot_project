import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpireSubscriptionsCommand:
    pass


@dataclass(frozen=True)
class GetSubscriptionCommand:
    user_id: uuid.UUID
