from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.product.entity import Product
from app.domain.product.repository import IProductRepository
from app.infrastructure.db.models import ProductModel


def _to_domain(row: ProductModel) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        description=row.description,
        price=row.price,
        stock_quantity=row.stock_quantity,
    )


class ProductRepository(IProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, product_id: int, *, for_update: bool = False) -> Product | None:
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def add(self, product: Product) -> Product:
        row = ProductModel(
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
        )
        self._session.add(row)
        await self._session.flush()
        return _to_domain(row)

    async def update_stock(self, product_id: int, new_stock: int) -> None:
        await self._session.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(stock_quantity=new_stock)
        )
