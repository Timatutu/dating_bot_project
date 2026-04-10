import uuid
from abc import ABC, abstractmethod

from src.domain.subscription.entity import Subscription


class ISubscriptionRepository(ABC):

    @abstractmethod
    async def save(self, subscription: Subscription) -> None: ...

    @abstractmethod
    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None: ...

    @abstractmethod
    async def get_active_by_user(self, user_id: uuid.UUID) -> Subscription | None: ...

    @abstractmethod
    async def get_expired(self) -> list[Subscription]: ...
