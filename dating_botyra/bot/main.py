import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

import common.db.models  

from bot.config import settings
from bot.middlewares.auth import AuthMiddleware
from bot.routers import match, profile, start, subscription, swipe
from bot.services.payment_client import PaymentClient

logging.basicConfig(level=logging.INFO)


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

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(swipe.router)
    dp.include_router(subscription.router)
    dp.include_router(match.router)

    await payment_client.start()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await payment_client.close()


if __name__ == "__main__":
    asyncio.run(main())
