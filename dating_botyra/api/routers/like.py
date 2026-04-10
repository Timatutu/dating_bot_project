from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from common.broker.publisher import publish_event
from common.db.crud.likes import check_mutual_like, create_like, get_like
from common.db.crud.matches import create_match, get_existing_match
from common.db.models.user import User
from common.db.session import get_db
from common.schemas.like import LikeCreate, LikeResult

router = APIRouter()


@router.post("/", response_model=LikeResult, status_code=status.HTTP_201_CREATED)
async def like_user(
    data: LikeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id == data.to_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like yourself")

    existing = await get_like(db, current_user.id, data.to_user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already voted")

    await create_like(db, current_user.id, data.to_user_id, data.action)
    await publish_event("like.event", {
        "from": str(current_user.id),
        "to": str(data.to_user_id),
        "action": data.action,
    })

    is_match = False
    match_id = None

    if data.action == "like":
        mutual = await check_mutual_like(db, current_user.id, data.to_user_id)
        if mutual:
            existing_match = await get_existing_match(db, current_user.id, data.to_user_id)
            if not existing_match:
                match = await create_match(db, current_user.id, data.to_user_id)
                match_id = match.id
                await publish_event("match.created", {
                    "user1": str(current_user.id),
                    "user2": str(data.to_user_id),
                    "match_id": str(match_id),
                })
            is_match = True

    return LikeResult(action=data.action, is_match=is_match, match_id=match_id)
