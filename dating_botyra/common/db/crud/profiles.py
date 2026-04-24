import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.db.models.profile import Profile
from common.db.models.rating import Rating


async def get_profile_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == user_id)
        .options(selectinload(Profile.photos))
    )
    return result.scalar_one_or_none()


async def create_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    age: int,
    gender: str,
    bio: str | None = None,
    city: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    photos_count: int = 0,
) -> Profile:
    profile = Profile(
        user_id=user_id,
        name=name,
        age=age,
        gender=gender,
        bio=bio,
        city=city,
        lat=lat,
        lng=lng,
        photos_count=photos_count,
    )
    db.add(profile)
    rating = Rating(user_id=user_id)
    db.add(rating)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, profile: Profile, **kwargs) -> Profile:
    for key, value in kwargs.items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def delete_profile(db: AsyncSession, profile: Profile) -> None:
    await db.delete(profile)
    await db.commit()
