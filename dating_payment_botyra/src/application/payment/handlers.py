import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.common.event_bus import IEventBus
from src.application.common.uow import IUnitOfWork
from src.application.payment.commands import (
    CheckCryptoPaymentCommand,
    ConfirmPaymentCommand,
    CreateCryptoPaymentCommand,
    CreatePaymentCommand,
)
from src.config import settings
from src.domain.payment.entity import Payment
from src.domain.payment.events import PaymentFailed, PaymentSucceeded
from src.domain.payment.value_objects import Money, PaymentStatus, Provider
from src.domain.subscription.entity import Subscription
from src.domain.subscription.service import activate_subscription
from src.domain.subscription.value_objects import PLAN_PRICE_STARS, PLAN_PRICE_USDT
from src.infrastructure.gateways.crypto.eth import EthUsdtGateway
from src.infrastructure.gateways.crypto.sol import SolUsdtGateway

logger = logging.getLogger(__name__)


@dataclass
class CreatePaymentResult:
    payment_id: uuid.UUID
    provider: str
    stars_amount: int | None = None  


class CreatePaymentHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, cmd: CreatePaymentCommand) -> CreatePaymentResult:
        async with self._uow:
            subscription = Subscription(user_id=cmd.user_id, plan=cmd.plan)
            await self._uow.subscriptions.save(subscription)
            stars = PLAN_PRICE_STARS[cmd.plan]
            payment = Payment(
                user_id=cmd.user_id,
                subscription_id=subscription.id,
                provider=cmd.provider,
                amount=Money(amount=stars, currency="XTR"),
            )
            await self._uow.payments.save(payment)
            await self._uow.commit()

        return CreatePaymentResult(
            payment_id=payment.id,
            provider=cmd.provider.value,
            stars_amount=stars,
        )


class ConfirmPaymentHandler:
    def __init__(self, uow: IUnitOfWork, event_bus: IEventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def handle(self, cmd: ConfirmPaymentCommand) -> None:
        async with self._uow:
            payment = await self._uow.payments.get_by_id(cmd.payment_id)
            if payment is None or payment.status != PaymentStatus.PENDING:
                return

            payment.succeed(cmd.provider_payment_id)

            subscription = await self._uow.subscriptions.get_by_id(payment.subscription_id)
            if subscription is None:
                payment.fail()
                await self._uow.payments.save(payment)
                await self._uow.commit()
                return

            event = activate_subscription(subscription)

            await self._uow.payments.save(payment)
            await self._uow.subscriptions.save(subscription)
            await self._uow.commit()

        await self._event_bus.publish(
            PaymentSucceeded(
                payment_id=payment.id,
                user_id=payment.user_id,
                subscription_id=subscription.id,
            )
        )
        await self._event_bus.publish(event)


@dataclass
class CreateCryptoPaymentResult:
    payment_id: uuid.UUID
    deposit_address: str
    usdt_amount: int          
    usdt_display: str      
    expires_at: str          


class CreateCryptoPaymentHandler:
    def __init__(
        self,
        uow: IUnitOfWork,
        eth_gateway: EthUsdtGateway,
        sol_gateway: SolUsdtGateway,
    ) -> None:
        self._uow = uow
        self._eth = eth_gateway
        self._sol = sol_gateway

    async def handle(self, cmd: CreateCryptoPaymentCommand) -> CreateCryptoPaymentResult:
        usdt_amount = PLAN_PRICE_USDT[cmd.plan]
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.crypto_payment_timeout_minutes
        )

        async with self._uow:
            subscription = Subscription(user_id=cmd.user_id, plan=cmd.plan)
            await self._uow.subscriptions.save(subscription)

            payment = Payment(
                user_id=cmd.user_id,
                subscription_id=subscription.id,
                provider=cmd.provider,
                amount=Money(amount=usdt_amount, currency="USDT"),
                expires_at=expires_at,
            )

            if cmd.provider == Provider.ETH:
                deposit_address = await self._eth.compute_deposit_address(payment.id)
            elif cmd.provider == Provider.SOL:
                deposit_address = await self._sol.derive_deposit_address(payment.id)
            else:
                raise ValueError(f"Unsupported crypto provider: {cmd.provider}")
            payment.deposit_address = deposit_address

            await self._uow.payments.save(payment)
            await self._uow.commit()

        return CreateCryptoPaymentResult(
            payment_id=payment.id,
            deposit_address=deposit_address,
            usdt_amount=usdt_amount,
            usdt_display=f"{usdt_amount / 1_000_000:.2f}",
            expires_at=expires_at.isoformat(),
        )


@dataclass
class CheckCryptoPaymentResult:
    status: str           
    tx_hash: str | None = None


class CheckCryptoPaymentHandler:
    def __init__(
        self,
        uow: IUnitOfWork,
        event_bus: IEventBus,
        eth_gateway: EthUsdtGateway,
        sol_gateway: SolUsdtGateway,
    ) -> None:
        self._uow = uow
        self._event_bus = event_bus
        self._eth = eth_gateway
        self._sol = sol_gateway

    async def handle(self, cmd: CheckCryptoPaymentCommand) -> CheckCryptoPaymentResult:
        async with self._uow:
            payment = await self._uow.payments.get_by_id(cmd.payment_id)
            if payment is None:
                return CheckCryptoPaymentResult(status="failed")

            if payment.status == PaymentStatus.SUCCEEDED:
                return CheckCryptoPaymentResult(
                    status="succeeded",
                    tx_hash=payment.provider_payment_id,
                )

            if payment.status == PaymentStatus.FAILED:
                return CheckCryptoPaymentResult(status="failed")

            if payment.is_expired:
                payment.fail()
                await self._uow.payments.save(payment)
                await self._uow.commit()
                await self._event_bus.publish(
                    PaymentFailed(payment_id=payment.id, user_id=payment.user_id)
                )
                return CheckCryptoPaymentResult(status="expired")

            if payment.provider == Provider.ETH:
                has_funds = await self._eth.has_sufficient_payment(
                    payment.deposit_address, payment.amount.amount
                )
            elif payment.provider == Provider.SOL:
                has_funds = await self._sol.has_sufficient_payment(
                    payment.id, payment.amount.amount
                )
            else:
                logger.warning("Unsupported payment provider: %s", payment.provider)
                return CheckCryptoPaymentResult(status="failed")
            if not has_funds:
                return CheckCryptoPaymentResult(status="pending")

            try:
                if payment.provider == Provider.ETH:
                    tx_hash = await self._eth.deploy_and_sweep(payment.id)
                elif payment.provider == Provider.SOL:
                    tx_hash = await self._sol.sweep(payment.id)
                else:
                    return CheckCryptoPaymentResult(status="failed")
            except Exception as exc:  
                logger.warning(
                    "deploy_and_sweep failed for payment %s (will stay pending): %s",
                    payment.id,
                    exc,
                )
                return CheckCryptoPaymentResult(status="pending")
            payment.succeed(tx_hash)

            subscription = await self._uow.subscriptions.get_by_id(payment.subscription_id)
            if subscription is not None:
                event = activate_subscription(subscription)
                await self._uow.subscriptions.save(subscription)
            else:
                event = None

            await self._uow.payments.save(payment)
            await self._uow.commit()

        await self._event_bus.publish(
            PaymentSucceeded(
                payment_id=payment.id,
                user_id=payment.user_id,
                subscription_id=payment.subscription_id,
            )
        )
        if event is not None:
            await self._event_bus.publish(event)

        return CheckCryptoPaymentResult(status="succeeded", tx_hash=tx_hash)
