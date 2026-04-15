from abc import ABC, abstractmethod

from app.domain.product.entity import Product


class IProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: int, *, for_update: bool = False) -> Product | None: ...

    @abstractmethod
    async def add(self, product: Product) -> Product: ...

    @abstractmethod
    async def update_stock(self, product_id: int, new_stock: int) -> None: ...
