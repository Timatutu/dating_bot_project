import logging
import uuid
from typing import Any

import grpc

from bot.generated import payment_pb2, payment_pb2_grpc

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    pass


class PaymentClient:
    def __init__(self, host: str, port: int = 50051) -> None:
        self._address = f"{host}:{port}"
        self._channel: grpc.aio.Channel | None = None
        self._stub: payment_pb2_grpc.PaymentServiceStub | None = None

    async def start(self) -> None:
        self._channel = grpc.aio.insecure_channel(self._address)
        self._stub = payment_pb2_grpc.PaymentServiceStub(self._channel)
        logger.info("PaymentClient connected to gRPC %s", self._address)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("PaymentClient disconnected")

    @property
    def stub(self) -> payment_pb2_grpc.PaymentServiceStub:
        if self._stub is None:
            raise RuntimeError("PaymentClient is not started. Call .start() first.")
        return self._stub


    async def get_subscription(self, user_id: uuid.UUID) -> dict[str, Any] | None:
        try:
            response: payment_pb2.GetSubscriptionResponse = await self.stub.GetSubscription(
                payment_pb2.GetSubscriptionRequest(user_id=str(user_id))
            )
            if not response.found:
                return None
            return {
                "subscription_id": response.subscription_id,
                "plan": response.plan,
                "status": response.status,
                "expires_at": response.expires_at or None,
                "is_active": response.is_active,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("GetSubscription failed: %s", exc.details())
            return None

    async def create_payment(
        self, user_id: uuid.UUID, plan: str
    ) -> tuple[str, int] | None:
        try:
            response: payment_pb2.CreatePaymentResponse = await self.stub.CreatePayment(
                payment_pb2.CreatePaymentRequest(
                    user_id=str(user_id),
                    plan=plan,
                    provider="tg_stars",
                )
            )
            return response.payment_id, response.stars_amount
        except grpc.aio.AioRpcError as exc:
            logger.error("CreatePayment failed: %s", exc.details())
            return None

    async def confirm_payment(self, payment_id: str, charge_id: str) -> bool:
        try:
            await self.stub.ConfirmPayment(
                payment_pb2.ConfirmPaymentRequest(
                    payment_id=payment_id,
                    provider_payment_id=charge_id,
                )
            )
            return True
        except grpc.aio.AioRpcError as exc:
            logger.error("ConfirmPayment failed: %s", exc.details())
            return False


    async def create_crypto_payment(
        self, user_id: uuid.UUID, plan: str, provider: str = "eth"
    ) -> dict[str, Any] | None:
        try:
            response: payment_pb2.CreateCryptoPaymentResponse = (
                await self.stub.CreateCryptoPayment(
                    payment_pb2.CreateCryptoPaymentRequest(
                        user_id=str(user_id),
                        plan=plan,
                        provider=provider,
                    )
                )
            )
            return {
                "payment_id": response.payment_id,
                "deposit_address": response.deposit_address,
                "usdt_amount": response.usdt_amount,
                "usdt_display": response.usdt_display,
                "expires_at": response.expires_at,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("CreateCryptoPayment failed: %s", exc.details())
            return None

    async def check_crypto_payment(self, payment_id: str) -> dict[str, Any] | None:
        try:
            response: payment_pb2.CheckCryptoPaymentResponse = (
                await self.stub.CheckCryptoPayment(
                    payment_pb2.CheckCryptoPaymentRequest(payment_id=payment_id)
                )
            )
            return {
                "status": response.status,
                "tx_hash": response.tx_hash or None,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("CheckCryptoPayment failed: %s", exc.details())
            return None
