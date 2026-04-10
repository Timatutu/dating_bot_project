import asyncio
import logging

from src.application.payment.commands import CheckCryptoPaymentCommand
from src.container import container
from src.domain.payment.value_objects import Provider
from src.infrastructure.db.repositories.payment import PaymentRepository
from src.infrastructure.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 30


async def crypto_payment_checker() -> None:
    logger.info("Crypto payment checker started (interval=%ss)", POLL_INTERVAL_SEC)

    while True:
        try:
            await _check_pending_payments()
        except asyncio.CancelledError:
            logger.info("Crypto payment checker stopped")
            return
        except Exception:
            logger.exception("Crypto payment checker error")

        await asyncio.sleep(POLL_INTERVAL_SEC)


async def _check_pending_payments() -> None:
    if not container.eth_gateway.is_available:
        return

    handler = container.check_crypto_payment_handler()

    async with AsyncSessionLocal() as session:
        repo = PaymentRepository(session)
        pending_payments = await repo.get_pending_by_provider(Provider.ETH.value)

    if not pending_payments:
        return

    logger.info("Checking %d pending crypto payments", len(pending_payments))

    for payment in pending_payments:
        try:
            result = await handler.handle(
                CheckCryptoPaymentCommand(payment_id=payment.id)
            )
            if result.status != "pending":
                logger.info(
                    "Payment %s -> %s (tx=%s)",
                    payment.id, result.status, result.tx_hash,
                )
        except Exception:
            logger.exception("Error checking payment %s", payment.id)
