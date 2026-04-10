import asyncio
import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("crypto_checker started (no crypto providers active yet)")
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run())
