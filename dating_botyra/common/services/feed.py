from __future__ import annotations

import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.db.models.like import Like
from common.db.models.profile import Profile
from common.db.models.rating import Rating


def _escape_ilike(frag: str) -> str:
    return frag.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


async def get_next_candidate(
    db: AsyncSession,
    viewer_user_id: uuid.UUID,
    *,
    preferred_gender: str,
    city_query: str,
) -> Profile | None:
    if preferred_gender not in ("male", "female"):
        return None
    city = city_query.strip()
    if not city:
        return None

    already = exists(
        select(Like.id).where(
            Like.from_user_id == viewer_user_id,
            Like.to_user_id == Profile.user_id,
        )
    )
    like_pattern = f"%{_escape_ilike(city)}%"
    statement = (
        select(Profile)
        .outerjoin(Rating, Rating.user_id == Profile.user_id)
        .where(Profile.user_id != viewer_user_id)
        .where(Profile.is_visible.is_(True))
        .where(Profile.gender == preferred_gender)
        .where(Profile.city.isnot(None))
        .where(Profile.city.ilike(like_pattern, escape="\\"))
        .where(~already)
        .options(selectinload(Profile.photos))
    )
    statement = statement.order_by(
        func.coalesce(Rating.combined_score, 0.0).desc(),
        func.random(),
    ).limit(1)

    result = await db.execute(statement)
    profile = result.scalars().first()
    if profile is not None:
        _ = list(profile.photos)
    return profile
