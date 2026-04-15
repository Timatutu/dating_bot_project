from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.shared.uow import IUnitOfWork
from app.infrastructure.db.repositories.customer import CustomerRepository
from app.infrastructure.db.repositories.order import OrderRepository
from app.infrastructure.db.repositories.product import ProductRepository


class SqlAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self._committed = False
        self.customers = CustomerRepository(self._session)
        self.products = ProductRepository(self._session)
        self.orders = OrderRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self._session is not None
        try:
            if exc_type is not None or not self._committed:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()
