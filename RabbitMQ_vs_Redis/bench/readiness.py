from __future__ import annotations

import asyncio
import time

import aio_pika
import redis.asyncio as redis

from bench.core import Settings


async def wait_for_rabbitmq(url: str, *, timeout_sec: float = 120.0, interval_sec: float = 1.0) -> None:
    deadline = time.monotonic() + timeout_sec
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            conn = await aio_pika.connect_robust(url)
            await conn.close()
            return
        except Exception as exc:
            last = exc
            await asyncio.sleep(interval_sec)
    raise RuntimeError(f"RabbitMQ not reachable at {url!r} after {timeout_sec}s: {last!r}")


async def wait_for_redis(url: str, *, timeout_sec: float = 60.0, interval_sec: float = 0.5) -> None:
    deadline = time.monotonic() + timeout_sec
    last: Exception | None = None
    while time.monotonic() < deadline:
        client = redis.from_url(url, decode_responses=False)
        try:
            pong = await client.ping()
            if pong:
                return
        except Exception as exc:
            last = exc
        finally:
            await client.aclose()
        await asyncio.sleep(interval_sec)
    raise RuntimeError(f"Redis not reachable at {url!r} after {timeout_sec}s: {last!r}")


async def wait_for_brokers(settings_: Settings, *, timeout_sec: float = 120.0) -> None:
    await asyncio.gather(
        wait_for_rabbitmq(settings_.rabbitmq_url, timeout_sec=timeout_sec),
        wait_for_redis(settings_.redis_url, timeout_sec=min(timeout_sec, 90.0)),
    )
