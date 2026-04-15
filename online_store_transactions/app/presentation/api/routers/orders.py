from fastapi import APIRouter, Depends, HTTPException, status

from app.application.customer.update_email import CustomerNotFoundError
from app.application.order.place_order import (
    OrderItemInput,
    PlaceOrderCommand,
    PlaceOrderUseCase,
    ProductNotFoundError,
)
from app.presentation.api.deps import get_place_order_use_case
from app.presentation.api.schemas import OrderCreate, OrderItemOut, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: OrderCreate,
    use_case: PlaceOrderUseCase = Depends(get_place_order_use_case),
) -> OrderOut:
    command = PlaceOrderCommand(
        customer_id=payload.customer_id,
        items=[OrderItemInput(product_id=i.product_id, quantity=i.quantity) for i in payload.items],
    )
    try:
        order = await use_case.execute(command)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return OrderOut(
        id=order.id,
        customer_id=order.customer_id,
        total_amount=order.total_amount,
        order_date=order.order_date,
        items=[
            OrderItemOut(product_id=i.product_id, quantity=i.quantity, price=i.price)
            for i in order.items
        ],
    )
