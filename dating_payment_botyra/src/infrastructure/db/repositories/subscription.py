import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.subscription.entity import Subscription
from src.domain.subscription.repository import ISubscriptionRepository
from src.domain.subscription.value_objects import Plan, SubscriptionStatus
from src.infrastructure.db.models.subscription import SubscriptionModel


def _to_domain(row: SubscriptionModel) -> Subscription:
    subscription = Subscription(id=row.id)
    subscription.user_id = row.user_id
    subscription.plan = Plan(row.plan)
    subscription.status = SubscriptionStatus(row.status)
    subscription.expires_at = row.expires_at
    subscription.created_at = row.created_at
    return subscription


def _to_model(subscription: Subscription) -> SubscriptionModel:
    return SubscriptionModel(
        id=subscription.id,
        user_id=subscription.user_id,
        plan=subscription.plan.value,
        status=subscription.status.value,
        expires_at=subscription.expires_at,
    )


class SubscriptionRepository(ISubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, subscription: Subscription) -> None:
        existing = await self._session.get(SubscriptionModel, subscription.id)
        if existing:
            existing.status = subscription.status.value
            existing.expires_at = subscription.expires_at
        else:
            self._session.add(_to_model(subscription))

    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None:
        row = await self._session.get(SubscriptionModel, subscription_id)
        return _to_domain(row) if row else None

    async def get_active_by_user(self, user_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == "active",
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_expired(self) -> list[Subscription]:
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.status == "active",
                SubscriptionModel.expires_at < datetime.now(timezone.utc),
            )
        )
        return [_to_domain(row) for row in result.scalars()]
