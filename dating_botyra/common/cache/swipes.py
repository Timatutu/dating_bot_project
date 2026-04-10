import uuid
from datetime import date, datetime, timezone, timedelta

import redis.asyncio as aioredis

from bot.config import settings

_redis: aioredis.Redis | None = None
FREE_SWIPES_PER_DAY = 50
SWIPE_KEY = "swipes:{user_id}:{date}"


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    midnight = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=1)
    return int(midnight.timestamp())


async def get_swipes_today(user_id: uuid.UUID) -> int:
    redis = _get_redis()
    key = SWIPE_KEY.format(user_id=user_id, date=date.today().isoformat())
    val = await redis.get(key)
    return int(val) if val else 0


async def increment_swipe(user_id: uuid.UUID) -> int:
    redis = _get_redis()
    key = SWIPE_KEY.format(user_id=user_id, date=date.today().isoformat())
    count = await redis.incr(key)
    if count == 1:
        await redis.expireat(key, _midnight_utc())
    return count


async def can_swipe(user_id: uuid.UUID, has_subscription: bool) -> bool:
    if has_subscription:
        return True
    count = await get_swipes_today(user_id)
    return count < FREE_SWIPES_PER_DAY


async def swipes_left(user_id: uuid.UUID) -> int:
    count = await get_swipes_today(user_id)
    return max(0, FREE_SWIPES_PER_DAY - count)
