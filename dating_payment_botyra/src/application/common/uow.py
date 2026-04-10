from abc import ABC, abstractmethod

from src.domain.payment.repository import IPaymentRepository
from src.domain.subscription.repository import ISubscriptionRepository


class IUnitOfWork(ABC):
    payments: IPaymentRepository
    subscriptions: ISubscriptionRepository

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    async def __aenter__(self) -> "IUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.rollback()
