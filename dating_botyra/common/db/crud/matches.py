import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.match import Match


def _ordered_user_ids(id_a: uuid.UUID, id_b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """Пара (user1_id, user2_id) в фиксированном порядке для уникальности в БД."""
    return (id_a, id_b) if str(id_a) < str(id_b) else (id_b, id_a)


async def find_match_between(
    db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
) -> Match | None:
    first_id, second_id = _ordered_user_ids(user_a, user_b)
    result = await db.execute(
        select(Match).where(Match.user1_id == first_id, Match.user2_id == second_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_match(
    db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
) -> Match:
    found = await find_match_between(db, user_a, user_b)
    if found is not None:
        return found
    first_id, second_id = _ordered_user_ids(user_a, user_b)
    new_match = Match(user1_id=first_id, user2_id=second_id, is_active=True)
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)
    return new_match
