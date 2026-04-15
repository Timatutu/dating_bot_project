from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Product
from app.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED, summary="Scenario 3: atomic product addition")
async def add_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    async with session.begin():
        product = Product(product_name=payload.product_name, price=payload.price)
        session.add(product)
        await session.flush()
        return ProductOut(
            product_id=product.product_id,
            product_name=product.product_name,
            price=product.price,
        )
