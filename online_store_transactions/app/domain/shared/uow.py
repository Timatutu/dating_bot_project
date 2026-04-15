from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.customer.repository import ICustomerRepository
    from app.domain.order.repository import IOrderRepository
    from app.domain.product.repository import IProductRepository


class IUnitOfWork(ABC):
    customers: "ICustomerRepository"
    products: "IProductRepository"
    orders: "IOrderRepository"

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
