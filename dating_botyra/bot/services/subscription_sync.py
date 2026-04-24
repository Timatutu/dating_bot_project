"""Синк даты окончания подписки в БД бота с payment-сервисом + пересчёт рейтинга (буст подписки)."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from bot.services.payment_client import PaymentClient
from common.db.crud.users import get_user_by_id, update_user
from common.db.session import AsyncSessionLocal
from common.services.rating_engine import recompute_rating_for_user

logger = logging.getLogger(__name__)


def _parse_expires(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    normalized: str = iso_str.replace("Z", "+00:00") if iso_str.endswith("Z") else iso_str
    return datetime.fromisoformat(normalized)


async def sync_subscription_from_payment(
    payment_client: PaymentClient, user_id: uuid.UUID
) -> None:
    try:
        sub = await payment_client.get_subscription(user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_subscription for sync: %s", exc)
        return
    async with AsyncSessionLocal() as db:
        user = await get_user_by_id(db, user_id)
        if user is None:
            return
        if sub and sub.get("is_active") and sub.get("expires_at"):
            exp = _parse_expires(sub["expires_at"])
        else:
            exp = None
        await update_user(db, user, sub_expires_at=exp)
        await recompute_rating_for_user(db, user_id)
