import asyncio
import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    from src.container import container
    handler = container.expire_subscriptions_handler()
    while True:
        try:
            count = await handler.handle()
            if count:
                logger.info("Expired %d subscriptions", count)
        except Exception:
            logger.exception("sub_expiry error")
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(run())
