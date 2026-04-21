from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractQueue, AbstractRobustConnection

from bench.core import Settings


class RabbitBroker:
    name = "rabbitmq"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._conn: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None

    async def connect(self) -> None:
        last: Exception | None = None
        for attempt in range(1, 31):
            try:
                self._conn = await aio_pika.connect_robust(self._settings.rabbitmq_url)
                break
            except Exception as exc:
                last = exc
                await asyncio.sleep(1.0)
        else:
            raise RuntimeError(
                f"RabbitMQ connect failed after retries: {last!r}"
            ) from last
        self._channel = await self._conn.channel(publisher_confirms=False)
        await self._channel.set_qos(prefetch_count=500)
        self._queue = await self._channel.declare_queue(
            self._settings.rabbitmq_queue, durable=False, auto_delete=False
        )

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            self._channel = None
            self._queue = None

    async def reset(self) -> None:
        assert self._queue is not None
        await self._queue.purge()

    async def publish(self, payload: bytes) -> None:
        assert self._channel is not None
        await self._channel.default_exchange.publish(
            aio_pika.Message(body=payload, delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT),
            routing_key=self._settings.rabbitmq_queue,
        )

    async def consume(self) -> AsyncIterator[bytes]:
        assert self._queue is not None
        async with self._queue.iterator() as it:
            async for message in it:
                async with message.process():
                    yield message.body
