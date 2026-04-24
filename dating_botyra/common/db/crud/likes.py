import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from common.db.models.like import Like


async def list_incoming_liker_ids(
    db: AsyncSession, to_user_id: uuid.UUID, *, limit: int = 20
) -> list[uuid.UUID]:
    result = await db.execute(
        select(Like)
        .where(Like.to_user_id == to_user_id, Like.action == "like")
        .order_by(Like.created_at.desc())
    )
    rows = list(result.scalars().all())
    seen: set[uuid.UUID] = set()
    out: list[uuid.UUID] = []
    for like in rows:
        if like.from_user_id in seen:
            continue
        seen.add(like.from_user_id)
        out.append(like.from_user_id)
        if len(out) >= limit:
            break
    return out


async def list_pending_incoming_liker_ids(
    db: AsyncSession, to_user_id: uuid.UUID, *, limit: int = 20
) -> list[uuid.UUID]:
    incoming = aliased(Like)
    outgoing = aliased(Like)
    statement = (
        select(
            incoming.from_user_id,
            func.max(incoming.created_at).label("last_like_at"),
        )
        .where(
            incoming.to_user_id == to_user_id,
            incoming.action == "like",
        )
        .where(
            ~exists(
                select(outgoing.id).where(
                    outgoing.from_user_id == to_user_id,
                    outgoing.to_user_id == incoming.from_user_id,
                )
            )
        )
        .group_by(incoming.from_user_id)
        .order_by(func.max(incoming.created_at).desc())
        .limit(limit)
    )
    result = await db.execute(statement)
    return [row.from_user_id for row in result.all()]


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
        select(func.count())
        .select_from(Like)
        .where(
            Like.to_user_id == user_id,
            Like.action == "like",
        )
    )
    return int(result.scalar_one() or 0)


async def get_pending_incoming_likes_count(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    incoming = aliased(Like)
    outgoing = aliased(Like)
    statement = (
        select(func.count(func.distinct(incoming.from_user_id)))
        .where(
            incoming.to_user_id == user_id,
            incoming.action == "like",
        )
        .where(
            ~exists(
                select(outgoing.id).where(
                    outgoing.from_user_id == user_id,
                    outgoing.to_user_id == incoming.from_user_id,
                )
            )
        )
    )
    result = await db.execute(statement)
    return int(result.scalar_one() or 0)


async def get_sent_swipes_last_24h(db: AsyncSession, user_id: uuid.UUID) -> int:
    since = datetime.now(UTC) - timedelta(hours=24)
    result = await db.execute(
        select(func.count())
        .select_from(Like)
        .where(
            Like.from_user_id == user_id,
            Like.created_at >= since,
        )
    )
    return int(result.scalar_one() or 0)


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
