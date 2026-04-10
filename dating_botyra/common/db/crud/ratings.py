import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.rating import Rating

SUBSCRIPTION_BOOST = 50.0
PRIMARY_WEIGHT = 0.4
BEHAVIORAL_WEIGHT = 0.6


async def get_rating(db: AsyncSession, user_id: uuid.UUID) -> Rating | None:
    result = await db.execute(select(Rating).where(Rating.user_id == user_id))
    return result.scalar_one_or_none()


def calc_combined(primary: float, behavioral: float, has_subscription: bool) -> float:
    boost = SUBSCRIPTION_BOOST if has_subscription else 0.0
    return primary * PRIMARY_WEIGHT + behavioral * BEHAVIORAL_WEIGHT + boost


async def update_rating(
    db: AsyncSession,
    rating: Rating,
    primary_score: float | None = None,
    behavioral_score: float | None = None,
    has_subscription: bool = False,
) -> Rating:
    if primary_score is not None:
        rating.primary_score = primary_score
    if behavioral_score is not None:
        rating.behavioral_score = behavioral_score
    rating.combined_score = calc_combined(
        rating.primary_score, rating.behavioral_score, has_subscription
    )
    await db.commit()
    await db.refresh(rating)
    return rating
