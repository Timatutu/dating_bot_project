import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.payment.entity import Payment
from src.domain.payment.repository import IPaymentRepository
from src.domain.payment.value_objects import Money, PaymentStatus, Provider
from src.infrastructure.db.models.payment import PaymentModel


def _to_domain(row: PaymentModel) -> Payment:
    payment = Payment(id=row.id)
    payment.user_id = row.user_id
    payment.subscription_id = row.subscription_id
    payment.provider = Provider(row.provider)
    payment.amount = Money(amount=row.amount, currency=row.currency)
    payment.status = PaymentStatus(row.status)
    payment.provider_payment_id = row.provider_payment_id
    payment.deposit_address = row.deposit_address
    payment.expires_at = row.expires_at
    payment.created_at = row.created_at
    return payment


def _to_model(payment: Payment) -> PaymentModel:
    return PaymentModel(
        id=payment.id,
        user_id=payment.user_id,
        subscription_id=payment.subscription_id,
        provider=payment.provider.value,
        amount=payment.amount.amount,
        currency=payment.amount.currency,
        status=payment.status.value,
        provider_payment_id=payment.provider_payment_id,
        deposit_address=payment.deposit_address,
        expires_at=payment.expires_at,
    )


class PaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment: Payment) -> None:
        existing = await self._session.get(PaymentModel, payment.id)
        if existing:
            existing.status = payment.status.value
            existing.provider_payment_id = payment.provider_payment_id
            existing.deposit_address = payment.deposit_address
            existing.expires_at = payment.expires_at
        else:
            self._session.add(_to_model(payment))

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        row = await self._session.get(PaymentModel, payment_id)
        return _to_domain(row) if row else None

    async def get_pending_by_provider(self, provider: str) -> list[Payment]:
        result = await self._session.execute(
            select(PaymentModel).where(
                PaymentModel.provider == provider,
                PaymentModel.status == "pending",
            )
        )
        return [_to_domain(row) for row in result.scalars()]
