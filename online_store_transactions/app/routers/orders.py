from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Customer, Order, OrderItem, Product
from app.schemas import OrderCreate, OrderItemOut, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="Scenario 1: place order transaction")
async def place_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    async with session.begin():
        customer = await session.get(Customer, payload.customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"customer {payload.customer_id} not found")

        order = Order(customer_id=payload.customer_id, order_date=datetime.now(timezone.utc), total_amount=0)
        session.add(order)
        await session.flush()

        total = 0
        items_out = []
        for item_in in payload.items:
            product = await session.get(Product, item_in.product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product {item_in.product_id} not found")

            subtotal = product.price * item_in.quantity
            total += subtotal

            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item_in.product_id,
                quantity=item_in.quantity,
                subtotal=subtotal,
            )
            session.add(order_item)
            await session.flush()

            items_out.append(OrderItemOut(
                product_id=item_in.product_id,
                quantity=item_in.quantity,
                subtotal=subtotal,
            ))

        await session.execute(
            update(Order).where(Order.order_id == order.order_id).values(total_amount=total)
        )

        return OrderOut(
            order_id=order.order_id,
            customer_id=order.customer_id,
            order_date=order.order_date,
            total_amount=total,
            items=items_out,
        )
