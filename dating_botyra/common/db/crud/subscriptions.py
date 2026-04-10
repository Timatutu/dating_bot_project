import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.payment import Payment
from common.db.models.subscription import Subscription
from common.db.models.user import User


async def create_subscription(
    db: AsyncSession, user_id: uuid.UUID, plan: str
) -> Subscription:
    sub = Subscription(user_id=user_id, plan=plan, status="pending")
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def get_active_subscription(db: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def activate_subscription(
    db: AsyncSession, sub: Subscription, expires_at: datetime, user: User
) -> Subscription:
    sub.status = "active"
    sub.expires_at = expires_at
    user.sub_expires_at = expires_at
    await db.commit()
    await db.refresh(sub)
    return sub


async def create_payment(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    amount: int,
    provider: str,
    provider_id: str | None = None,
) -> Payment:
    payment = Payment(
        subscription_id=subscription_id,
        amount=amount,
        provider=provider,
        provider_id=provider_id,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def confirm_payment(db: AsyncSession, payment: Payment) -> Payment:
    payment.status = "succeeded"
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment_by_provider_id(
    db: AsyncSession, provider: str, provider_id: str
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(
            Payment.provider == provider,
            Payment.provider_id == provider_id,
        )
    )
    return result.scalar_one_or_none()
