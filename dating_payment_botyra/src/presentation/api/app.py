import asyncio
import logging
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI

from src.application.common.event_bus import IEventBus
from src.config import settings
from src.container import container
from src.domain.shared.events import DomainEvent
from src.infrastructure.broker.publisher import RabbitMQEventBus
from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.db.uow import SqlAlchemyUoW
from src.infrastructure.gateways.crypto.checker import crypto_payment_checker
from src.infrastructure.gateways.crypto.eth import EthUsdtGateway
from src.infrastructure.gateways.http_client import HttpClient
from src.presentation.grpc.server import start_grpc_server, stop_grpc_server

logger = logging.getLogger(__name__)


class _NoopEventBus(IEventBus):
    async def publish(self, event: DomainEvent) -> None:
        logger.info("EVENT (noop): %s %s", type(event).__name__, vars(event))


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = None
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        event_bus = RabbitMQEventBus(connection)
        logger.info("RabbitMQ connected")
    except Exception as exc:
        logger.warning("RabbitMQ unavailable (%s), events will be logged only", exc)
        event_bus = _NoopEventBus()

    http_client = HttpClient()
    await http_client.start()

    eth_gateway = EthUsdtGateway()
    await eth_gateway.start()

    def make_uow() -> SqlAlchemyUoW:
        return SqlAlchemyUoW(AsyncSessionLocal())

    container.init(make_uow, event_bus, http_client, eth_gateway)

    checker_task = None
    if eth_gateway.is_available:
        checker_task = asyncio.create_task(crypto_payment_checker())
    grpc_server = await start_grpc_server()

    try:
        yield
    finally:
        await stop_grpc_server(grpc_server)

        if checker_task is not None:
            checker_task.cancel()
            try:
                await checker_task
            except asyncio.CancelledError:
                pass

        await http_client.close()
        if connection:
            await connection.close()


app = FastAPI(title="lovebinto payment service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
