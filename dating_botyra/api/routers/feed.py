from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends
from sqlalchemy import and_, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from common.db.models.like import Like
from common.db.models.profile import Profile
from common.db.models.rating import Rating
from common.db.models.user import User
from common.db.session import get_db
from common.schemas.profile import ProfileOut

router = APIRouter()

FEED_LIMIT = 10


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    EARTH_RADIUS_KM = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    haversine_a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(haversine_a))


@router.get("/", response_model=list[ProfileOut])
async def get_feed(
    gender: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    max_distance_km: float | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seen_subq = select(Like.to_user_id).where(Like.from_user_id == current_user.id)

    current_profile_result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    current_profile = current_profile_result.scalar_one_or_none()

    conditions = [
        Profile.user_id != current_user.id,
        Profile.is_visible == True,
        not_(Profile.user_id.in_(seen_subq)),
    ]

    if gender:
        conditions.append(Profile.gender == gender)
    if min_age:
        conditions.append(Profile.age >= min_age)
    if max_age:
        conditions.append(Profile.age <= max_age)

    result = await db.execute(
        select(Profile)
        .join(Rating, Rating.user_id == Profile.user_id, isouter=True)
        .where(and_(*conditions))
        .order_by(Rating.combined_score.desc().nulls_last())
        .limit(FEED_LIMIT * 3)
    )
    profiles = list(result.scalars().all())

    if max_distance_km and current_profile and current_profile.lat and current_profile.lng:
        profiles = [
            p for p in profiles
            if p.lat and p.lng
            and haversine(current_profile.lat, current_profile.lng, p.lat, p.lng) <= max_distance_km
        ]

    return profiles[:FEED_LIMIT]
