import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.crud.subscriptions import (
    activate_subscription,
    confirm_payment,
    create_payment,
    get_payment_by_provider_id,
)
from common.db.crud.users import get_user_by_id
from common.db.session import get_db
from common.schemas.subscription import PaymentOut

router = APIRouter()

PLAN_DURATION = {"monthly": 30, "yearly": 365}


@router.post("/yookassa", status_code=status.HTTP_200_OK)
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    event = payload.get("event")
    if event != "payment.succeeded":
        return {"status": "ignored"}

    obj = payload["object"]
    provider_id = obj["id"]
    metadata = obj.get("metadata", {})
    sub_id = metadata.get("subscription_id")
    user_id = metadata.get("user_id")

    if not sub_id or not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing metadata")

    payment = await get_payment_by_provider_id(db, "yookassa", provider_id)
    if payment and payment.status == "succeeded":
        return {"status": "already_processed"}

    if payment is None:
        payment = await create_payment(
            db,
            subscription_id=uuid.UUID(sub_id),
            amount=int(obj["amount"]["value"].replace(".", "")),
            provider="yookassa",
            provider_id=provider_id,
        )

    await confirm_payment(db, payment)

    sub = payment.subscription
    user = await get_user_by_id(db, uuid.UUID(user_id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=PLAN_DURATION.get(sub.plan, 30))
    await activate_subscription(db, sub, expires_at, user)

    return {"status": "ok"}
