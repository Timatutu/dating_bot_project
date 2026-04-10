import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.match import Match


async def create_match(db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID) -> Match:
    match = Match(user1_id=user1_id, user2_id=user2_id)
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


async def get_match_by_id(db: AsyncSession, match_id: uuid.UUID) -> Match | None:
    result = await db.execute(select(Match).where(Match.id == match_id))
    return result.scalar_one_or_none()


async def get_matches_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Match]:
    result = await db.execute(
        select(Match).where(
            or_(Match.user1_id == user_id, Match.user2_id == user_id),
            Match.is_active == True,
        )
    )
    return list(result.scalars().all())


async def get_existing_match(
    db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID
) -> Match | None:
    result = await db.execute(
        select(Match).where(
            or_(
                (Match.user1_id == user1_id) & (Match.user2_id == user2_id),
                (Match.user1_id == user2_id) & (Match.user2_id == user1_id),
            )
        )
    )
    return result.scalar_one_or_none()
