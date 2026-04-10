import uuid
from abc import ABC, abstractmethod

from src.domain.payment.entity import Payment


class IPaymentRepository(ABC):

    @abstractmethod
    async def save(self, payment: Payment) -> None: ...

    @abstractmethod
    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None: ...

    @abstractmethod
    async def get_pending_by_provider(self, provider: str) -> list[Payment]: ...
