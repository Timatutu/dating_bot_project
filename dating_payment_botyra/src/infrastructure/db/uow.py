from sqlalchemy.ext.asyncio import AsyncSession

from src.application.common.uow import IUnitOfWork
from src.infrastructure.db.repositories.payment import PaymentRepository
from src.infrastructure.db.repositories.subscription import SubscriptionRepository


class SqlAlchemyUoW(IUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.payments = PaymentRepository(session)
        self.subscriptions = SubscriptionRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aexit__(self, *args: object) -> None:
        await self.rollback()
        await self._session.close()
