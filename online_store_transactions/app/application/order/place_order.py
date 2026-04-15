from dataclasses import dataclass

from app.application.customer.update_email import CustomerNotFoundError
from app.domain.order.entity import Order
from app.domain.shared.uow import IUnitOfWork


class ProductNotFoundError(Exception):
    pass


@dataclass
class OrderItemInput:
    product_id: int
    quantity: int


@dataclass
class PlaceOrderCommand:
    customer_id: int
    items: list[OrderItemInput]


class PlaceOrderUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, command: PlaceOrderCommand) -> Order:
        if not command.items:
            raise ValueError("order must contain at least one item")

        async with self._uow as uow:
            customer = await uow.customers.get_by_id(command.customer_id)
            if customer is None:
                raise CustomerNotFoundError(f"customer {command.customer_id} not found")

            order = Order(id=None, customer_id=customer.id)

            for item_input in command.items:
                product = await uow.products.get_by_id(item_input.product_id, for_update=True)
                if product is None:
                    raise ProductNotFoundError(f"product {item_input.product_id} not found")

                product.decrease_stock(item_input.quantity)
                await uow.products.update_stock(product.id, product.stock_quantity)
                order.add_item(product.id, item_input.quantity, product.price)

            saved = await uow.orders.add(order)
            await uow.commit()
            return saved
