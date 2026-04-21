from __future__ import annotations

from collections.abc import AsyncIterator

from redis.asyncio import Redis

from bench.core import Settings


class RedisBroker:
    name = "redis"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._r: Redis | None = None
        self._queue_name: str = settings.redis_stream

    async def connect(self) -> None:
        self._r = Redis.from_url(self._settings.redis_url)
        await self._r.ping() 

    async def close(self) -> None:
        if self._r is not None:
            await self._r.aclose()
            self._r = None

    async def reset(self) -> None:
        assert self._r is not None
        await self._r.delete(self._queue_name)

    async def publish(self, payload: bytes) -> None:
        assert self._r is not None
        await self._r.lpush(self._queue_name, payload)

    async def consume(self) -> AsyncIterator[bytes]:
        assert self._r is not None
        
        while True:

            result = await self._r.brpop(self._queue_name, timeout=1)
            
            if result is None:
                continue
            
            _, raw_message = result
            
            payload = raw_message.encode() if isinstance(raw_message, str) else raw_message
            
            yield payload

