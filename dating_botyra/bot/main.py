import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

import common.db.models

from bot.config import settings
from bot.middlewares.auth import AuthMiddleware
from bot.routers import match, profile, start, subscription, swipe
from bot.services.payment_client import PaymentClient
from common.messaging.rabbit_publisher import close_rabbit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(AuthMiddleware())

    payment_client = PaymentClient(
        host=settings.payment_service_host,
        port=settings.payment_service_grpc_port,
    )
    dp["payment_client"] = payment_client

    @dp.error()
    async def on_handler_error(event: ErrorEvent) -> bool:
        logger.exception("Handler failed: %s", event.exception)
        update = event.update
        try:
            if update.message is not None:
                await update.message.answer(
                    "⚠️ Внутренняя ошибка. Чаще всего: не запущены PostgreSQL/Redis "
                    "или не сделан <code>alembic upgrade head</code> "
                    "или в .env указан хост <code>postgres</code>, а бот крутится вне Docker — "
                    "нужен <code>127.0.0.1</code> (см. <code>docker-compose.infra.yml</code> в "
                    "корне <code>dating_bot_project</code>)."
                )
            elif update.callback_query is not None and update.callback_query.message is not None:
                await update.callback_query.answer(
                    "Ошибка на сервере, см. логи бота.",
                    show_alert=True,
                )
        except Exception as send_exc: 
            logger.error("Failed to send error to user: %s", send_exc)
        return True

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(subscription.router)
    dp.include_router(match.router)
    dp.include_router(swipe.router)

    try:
        await payment_client.start()
    except Exception as exc: 
        logger.warning("gRPC payment client start failed: %s (крипто-оплата может быть недоступна)", exc)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_rabbit()
        await payment_client.close()


if __name__ == "__main__":
    asyncio.run(main())
