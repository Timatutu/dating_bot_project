import logging
import uuid

import grpc

from src.application.payment.commands import (
    CheckCryptoPaymentCommand,
    ConfirmPaymentCommand,
    CreateCryptoPaymentCommand,
    CreatePaymentCommand,
)
from src.container import container
from src.domain.payment.value_objects import Provider
from src.domain.subscription.value_objects import Plan
from src.generated import payment_pb2, payment_pb2_grpc

logger = logging.getLogger(__name__)


class PaymentServicer(payment_pb2_grpc.PaymentServiceServicer):

    async def CreatePayment(
        self,
        request: payment_pb2.CreatePaymentRequest,
        context: grpc.aio.ServicerContext,
    ) -> payment_pb2.CreatePaymentResponse:
        try:
            handler = container.create_payment_handler()
            result = await handler.handle(
                CreatePaymentCommand(
                    user_id=uuid.UUID(request.user_id),
                    plan=Plan(request.plan),
                    provider=Provider(request.provider),
                )
            )
            return payment_pb2.CreatePaymentResponse(
                payment_id=str(result.payment_id),
                provider=result.provider,
                stars_amount=result.stars_amount or 0,
            )
        except Exception as exc:
            logger.exception("CreatePayment error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def ConfirmPayment(
        self,
        request: payment_pb2.ConfirmPaymentRequest,
        context: grpc.aio.ServicerContext,
    ) -> payment_pb2.ConfirmPaymentResponse:
        try:
            handler = container.confirm_payment_handler()
            await handler.handle(
                ConfirmPaymentCommand(
                    payment_id=uuid.UUID(request.payment_id),
                    provider_payment_id=request.provider_payment_id,
                )
            )
            return payment_pb2.ConfirmPaymentResponse(status="ok")
        except Exception as exc:
            logger.exception("ConfirmPayment error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def GetSubscription(
        self,
        request: payment_pb2.GetSubscriptionRequest,
        context: grpc.aio.ServicerContext,
    ) -> payment_pb2.GetSubscriptionResponse:
        try:
            handler = container.get_subscription_handler()
            view = await handler.handle(uuid.UUID(request.user_id))
            if view is None:
                return payment_pb2.GetSubscriptionResponse(found=False)
            return payment_pb2.GetSubscriptionResponse(
                found=True,
                subscription_id=str(view.subscription_id),
                plan=view.plan,
                status=view.status,
                expires_at=view.expires_at.isoformat() if view.expires_at else "",
                is_active=view.is_active,
            )
        except Exception as exc:
            logger.exception("GetSubscription error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def CreateCryptoPayment(
        self,
        request: payment_pb2.CreateCryptoPaymentRequest,
        context: grpc.aio.ServicerContext,
    ) -> payment_pb2.CreateCryptoPaymentResponse:
        if not container.eth_gateway.is_available:
            await context.abort(
                grpc.StatusCode.UNAVAILABLE, "Crypto payments are not configured"
            )
            return

        try:
            handler = container.create_crypto_payment_handler()
            result = await handler.handle(
                CreateCryptoPaymentCommand(
                    user_id=uuid.UUID(request.user_id),
                    plan=Plan(request.plan),
                    provider=Provider(request.provider),
                )
            )
            return payment_pb2.CreateCryptoPaymentResponse(
                payment_id=str(result.payment_id),
                deposit_address=result.deposit_address,
                usdt_amount=result.usdt_amount,
                usdt_display=result.usdt_display,
                expires_at=result.expires_at,
            )
        except Exception as exc:
            logger.exception("CreateCryptoPayment error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def CheckCryptoPayment(
        self,
        request: payment_pb2.CheckCryptoPaymentRequest,
        context: grpc.aio.ServicerContext,
    ) -> payment_pb2.CheckCryptoPaymentResponse:
        try:
            handler = container.check_crypto_payment_handler()
            result = await handler.handle(
                CheckCryptoPaymentCommand(payment_id=uuid.UUID(request.payment_id))
            )
            return payment_pb2.CheckCryptoPaymentResponse(
                status=result.status,
                tx_hash=result.tx_hash or "",
            )
        except Exception as exc:
            logger.exception("CheckCryptoPayment error")
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
