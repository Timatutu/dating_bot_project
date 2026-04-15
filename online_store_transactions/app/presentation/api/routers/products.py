from fastapi import APIRouter, Depends, HTTPException, status

from app.application.product.add_product import AddProductCommand, AddProductUseCase
from app.presentation.api.deps import get_add_product_use_case
from app.presentation.api.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def add_product(
    payload: ProductCreate,
    use_case: AddProductUseCase = Depends(get_add_product_use_case),
) -> ProductOut:
    try:
        product = await use_case.execute(
            AddProductCommand(
                name=payload.name,
                description=payload.description,
                price=payload.price,
                stock_quantity=payload.stock_quantity,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
    )
