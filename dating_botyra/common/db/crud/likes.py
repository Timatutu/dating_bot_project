import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from common.db.models.like import Like


async def get_like(db: AsyncSession, from_user_id: uuid.UUID, to_user_id: uuid.UUID) -> Like | None:
    result = await db.execute(
        select(Like).where(Like.from_user_id == from_user_id, Like.to_user_id == to_user_id)
    )
    return result.scalar_one_or_none()


async def create_like(
    db: AsyncSession, from_user_id: uuid.UUID, to_user_id: uuid.UUID, action: str
) -> Like:
    like = Like(from_user_id=from_user_id, to_user_id=to_user_id, action=action)
    db.add(like)
    await db.commit()
    await db.refresh(like)
    return like


async def get_likes_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).where(
            Like.to_user_id == user_id,
            Like.action == "like",
        )
    )
    return result.scalar_one() or 0


async def check_mutual_like(
    db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
) -> bool:
    result = await db.execute(
        select(Like).where(
            Like.from_user_id == user_b,
            Like.to_user_id == user_a,
            Like.action == "like",
        )
    )
    return result.scalar_one_or_none() is not None
