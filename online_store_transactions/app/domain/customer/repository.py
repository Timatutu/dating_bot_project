from abc import ABC, abstractmethod

from app.domain.customer.entity import Customer


class ICustomerRepository(ABC):
    @abstractmethod
    async def get_by_id(self, customer_id: int) -> Customer | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Customer | None: ...

    @abstractmethod
    async def add(self, customer: Customer) -> Customer: ...

    @abstractmethod
    async def update_email(self, customer_id: int, new_email: str) -> Customer: ...
