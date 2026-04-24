"""Rabbit consumer: идемпотентный пересчёт рейтинга по событиям свайпа (см. dating_bot_project/README.md)."""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from typing import Any

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractIncomingMessage

try:
    from bot.config import settings
except Exception:  # noqa: BLE001
    from api.config import settings

from common.db.session import AsyncSessionLocal
from common.services.rating_engine import recompute_rating_for_user

logger = logging.getLogger(__name__)

EXCHANGE = "dating"
QUEUE = "dating.rating"
ROUTING = "swipe.*"


async def _handle(data: dict[str, Any]) -> None:
    try:
        uid_from = uuid.UUID(data["from_user_id"])
        uid_to = uuid.UUID(data["to_user_id"])
    except (KeyError, ValueError) as e:
        logger.warning("bad payload %s (%s)", data, e)
        return
    async with AsyncSessionLocal() as db:
        await recompute_rating_for_user(db, uid_from)
    async with AsyncSessionLocal() as db:
        await recompute_rating_for_user(db, uid_to)
    logger.info("recomputed for %s and %s", uid_from, uid_to)


async def on_swipe_event(incoming: AbstractIncomingMessage) -> None:
    async with incoming.process(requeue=False):
        body = incoming.body.decode("utf-8")
        data = json.loads(body)
        await _handle(data)


async def run_consumer() -> None:
    if not settings.rabbitmq_url:
        raise SystemExit("RABBITMQ_URL is empty")
    logging.basicConfig(level=logging.INFO)
    connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=10)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=4)
    exchange = await channel.declare_exchange(EXCHANGE, ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=ROUTING)
    await queue.consume(on_swipe_event)
    logger.info("queue=%s bound %s exchange=%s", QUEUE, ROUTING, EXCHANGE)
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        await connection.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(run_consumer())
    except KeyboardInterrupt:
        pass
