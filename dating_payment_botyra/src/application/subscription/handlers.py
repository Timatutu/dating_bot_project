import uuid

from src.application.common.event_bus import IEventBus
from src.application.common.uow import IUnitOfWork
from src.application.subscription.queries import SubscriptionView
from src.domain.subscription.service import expire_subscription


class GetSubscriptionHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, user_id: uuid.UUID) -> SubscriptionView | None:
        async with self._uow:
            sub = await self._uow.subscriptions.get_active_by_user(user_id)
            if sub is None:
                return None
            return SubscriptionView(
                subscription_id=sub.id,
                plan=sub.plan.value,
                status=sub.status.value,
                expires_at=sub.expires_at,
                is_active=sub.is_active,
            )


class ExpireSubscriptionsHandler:
    def __init__(self, uow: IUnitOfWork, event_bus: IEventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def handle(self) -> int:
        expired_count = 0
        async with self._uow:
            expired = await self._uow.subscriptions.get_expired()
            for sub in expired:
                event = expire_subscription(sub)
                await self._uow.subscriptions.save(sub)
                await self._event_bus.publish(event)
            await self._uow.commit()
            expired_count = len(expired)
        return expired_count
