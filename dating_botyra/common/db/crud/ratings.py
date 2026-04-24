import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.rating import Rating


async def get_rating_for_user(db: AsyncSession, user_id: uuid.UUID) -> Rating | None:
    r = await db.execute(select(Rating).where(Rating.user_id == user_id))
    return r.scalar_one_or_none()
