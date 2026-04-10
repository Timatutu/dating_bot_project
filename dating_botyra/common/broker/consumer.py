import asyncio
import json
import logging
from collections.abc import Callable, Awaitable

import aio_pika

from api.config import settings

logger = logging.getLogger(__name__)


async def consume(queue_name: str, handler: Callable[[dict], Awaitable[None]]) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(requeue=False):
                    try:
                        payload = json.loads(message.body.decode())
                        await handler(payload)
                    except Exception:
                        logger.exception(
                            "Error handling message from %s: %s",
                            queue_name,
                            message.body,
                        )
