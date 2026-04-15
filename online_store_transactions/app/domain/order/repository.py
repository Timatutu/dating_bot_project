from abc import ABC, abstractmethod

from app.domain.order.entity import Order


class IOrderRepository(ABC):
    @abstractmethod
    async def add(self, order: Order) -> Order: ...

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None: ...
