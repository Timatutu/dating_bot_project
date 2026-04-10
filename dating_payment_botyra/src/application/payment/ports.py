from abc import ABC, abstractmethod

from src.domain.payment.entity import Payment


class IPaymentGateway(ABC):
    @abstractmethod
    async def create(self, payment: Payment) -> dict: ...
