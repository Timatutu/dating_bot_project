from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.order.entity import Order, OrderItem
from app.domain.order.repository import IOrderRepository
from app.infrastructure.db.models import OrderItemModel, OrderModel


def _item_to_domain(row: OrderItemModel) -> OrderItem:
    return OrderItem(
        id=row.id,
        order_id=row.order_id,
        product_id=row.product_id,
        quantity=row.quantity,
        price=row.price,
    )


def _to_domain(row: OrderModel) -> Order:
    return Order(
        id=row.id,
        customer_id=row.customer_id,
        total_amount=row.total_amount,
        order_date=row.order_date,
        items=[_item_to_domain(i) for i in row.items],
    )


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> Order:
        row = OrderModel(
            customer_id=order.customer_id,
            total_amount=order.total_amount,
            order_date=order.order_date,
            items=[
                OrderItemModel(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
                for item in order.items
            ],
        )
        self._session.add(row)
        await self._session.flush()
        return _to_domain(row)

    async def get_by_id(self, order_id: int) -> Order | None:
        row = await self._session.get(OrderModel, order_id)
        return _to_domain(row) if row else None
