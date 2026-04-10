from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from common.db.crud.subscriptions import create_subscription, get_active_subscription
from common.db.models.user import User
from common.db.session import get_db
from common.schemas.subscription import SubscriptionCreate, SubscriptionOut

router = APIRouter()


@router.get("/active", response_model=SubscriptionOut | None)
async def get_my_active_sub(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_active_subscription(db, current_user.id)


@router.post("/", response_model=SubscriptionOut, status_code=201)
async def create_sub(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_subscription(db, user_id=current_user.id, plan=data.plan)
