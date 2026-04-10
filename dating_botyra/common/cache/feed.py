import json
import uuid

import redis.asyncio as aioredis

from bot.config import settings

_redis: aioredis.Redis | None = None
FEED_TTL = 300 
FEED_KEY = "feed:{user_id}"


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_feed_cache(user_id: uuid.UUID) -> list[str] | None:
    redis = _get_redis()
    key = FEED_KEY.format(user_id=user_id)
    data = await redis.get(key)
    if data is None:
        return None
    return json.loads(data)


async def set_feed_cache(user_id: uuid.UUID, profile_ids: list[str]) -> None:
    redis = _get_redis()
    key = FEED_KEY.format(user_id=user_id)
    await redis.set(key, json.dumps(profile_ids), ex=FEED_TTL)


async def invalidate_feed_cache(user_id: uuid.UUID) -> None:
    redis = _get_redis()
    key = FEED_KEY.format(user_id=user_id)
    await redis.delete(key)
