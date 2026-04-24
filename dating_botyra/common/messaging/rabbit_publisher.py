from __future__ import annotations

import contextlib
import json
import logging
import uuid
from typing import Any

import aio_pika
from aio_pika import ExchangeType

try:
    from bot.config import settings
except Exception:  
    from api.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def _ensure_channel() -> aio_pika.abc.AbstractExchange | None:
    global _connection, _channel, _exchange
    if not settings.rabbitmq_url:
        return None
    if _exchange is not None:
        return _exchange
    try:
        _connection = await aio_pika.connect_robust(
            settings.rabbitmq_url, timeout=5
        )
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            "dating", ExchangeType.TOPIC, durable=True
        )
        return _exchange
    except Exception as exc: 
        logger.warning("RabbitMQ connect failed, events not published: %s", exc)
        return None


async def publish_swipe_event(
    *,
    action: str,
    from_user_id: uuid.UUID,
    to_user_id: uuid.UUID,
    created_match: bool = False,
) -> None:
    ex = await _ensure_channel()
    if ex is None:
        return
    payload: dict[str, Any] = {
        "event": "swipe",
        "action": action,
        "from_user_id": str(from_user_id),
        "to_user_id": str(to_user_id),
        "created_match": created_match,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    await ex.publish(
        aio_pika.Message(body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=f"swipe.{action}",
    )
    logger.debug("Published swipe.%s for %s -> %s", action, from_user_id, to_user_id)


async def close_rabbit() -> None:
    global _connection, _channel, _exchange
    with contextlib.suppress(Exception):
        if _channel is not None and not _channel.is_closed:
            await _channel.close()
    with contextlib.suppress(Exception):
        if _connection is not None and not _connection.is_closed:
            await _connection.close()
    _connection = None
    _channel = None
    _exchange = None
