"""Рейтинг: primary (анкета + буст подписки), behavioral (лайки/мэтчи), combined — см. dating_bot_project/README.md."""
from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.like import Like
from common.db.models.match import Match
from common.db.models.profile import Profile
from common.db.models.rating import Rating
from common.db.models.user import User

# Активная подписка (users.sub_expires_at) увеличивает primary в ленте (визуальный «приоритет»)
SUBSCRIPTION_PRIMARY_BONUS = 0.12


def primary_from_profile(profile: Profile) -> float:
    score = 0.0
    if profile.name and len(profile.name.strip()) >= 2:
        score += 0.15
    if profile.bio:
        bio_len = len(profile.bio.strip())
        score += 0.1 if bio_len < 10 else 0.25
    if profile.city and len(profile.city.strip()) >= 2:
        score += 0.15
    if profile.photos_count > 0:
        score += min(0.35, 0.12 * min(profile.photos_count, 3))
    if 18 <= profile.age <= 90:
        score += 0.1
    return min(1.0, score)


async def _incoming_likes_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Like)
        .where(Like.to_user_id == user_id, Like.action == "like")
    )
    return int(result.scalar_one() or 0)


async def _matches_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Match)
        .where((Match.user1_id == user_id) | (Match.user2_id == user_id))
    )
    return int(result.scalar_one() or 0)


async def behavioral_from_stats(
    db: AsyncSession, user_id: uuid.UUID, profile: Profile | None
) -> float:
    likes_in = await _incoming_likes_count(db, user_id)
    matches_n = await _matches_count(db, user_id)
    # мягкое насыщение: лайки и мэтчи «тянут» behavioral вверх
    like_part = 1.0 - math.exp(-likes_in / 6.0)
    match_part = 1.0 - math.exp(-matches_n / 4.0)
    # лёгкий бонус за заполненную анкету (поощрение за «старательность»)
    fill = 0.0
    if profile and profile.bio and len(profile.bio) > 20:
        fill += 0.05
    raw = 0.55 * like_part + 0.40 * match_part + fill
    return min(1.0, max(0.0, raw))


def _subscription_active(ends: datetime | None) -> bool:
    if ends is None:
        return False
    now = datetime.now(UTC)
    e = ends if ends.tzinfo is not None else ends.replace(tzinfo=UTC)
    return e > now


async def recompute_rating_for_user(db: AsyncSession, user_id: uuid.UUID) -> Rating | None:
    result = await db.execute(select(Rating).where(Rating.user_id == user_id))
    rating = result.scalar_one_or_none()
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    result = await db.execute(select(User).where(User.id == user_id))
    user_row = result.scalar_one_or_none()

    primary = primary_from_profile(profile) if profile else 0.0
    if user_row and _subscription_active(user_row.sub_expires_at):
        primary = min(1.0, primary + SUBSCRIPTION_PRIMARY_BONUS)

    behavioral = await behavioral_from_stats(db, user_id, profile)
    combined = 0.35 * primary + 0.65 * behavioral

    if rating is None:
        rating = Rating(
            user_id=user_id,
            primary_score=primary,
            behavioral_score=behavioral,
            combined_score=combined,
        )
        db.add(rating)
    else:
        rating.primary_score = primary
        rating.behavioral_score = behavioral
        rating.combined_score = combined
    await db.commit()
    await db.refresh(rating)
    return rating
