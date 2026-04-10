import json

import aio_pika

from api.config import settings

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.RobustChannel | None = None


async def _get_channel() -> aio_pika.RobustChannel:
    global _connection, _channel
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel()
    return _channel


async def publish_event(routing_key: str, payload: dict) -> None:
    channel = await _get_channel()

    await channel.declare_queue(routing_key, durable=True)

    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        ),
        routing_key=routing_key,
    )
