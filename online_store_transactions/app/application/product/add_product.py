from dataclasses import dataclass
from decimal import Decimal

from app.domain.product.entity import Product
from app.domain.shared.uow import IUnitOfWork


@dataclass
class AddProductCommand:
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int


class AddProductUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, command: AddProductCommand) -> Product:
        if command.price < 0:
            raise ValueError("price must be non-negative")
        if command.stock_quantity < 0:
            raise ValueError("stock_quantity must be non-negative")

        product = Product(
            id=None,
            name=command.name.strip(),
            description=command.description,
            price=command.price,
            stock_quantity=command.stock_quantity,
        )

        async with self._uow as uow:
            saved = await uow.products.add(product)
            await uow.commit()
            return saved
