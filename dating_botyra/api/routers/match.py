import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from common.db.crud.matches import get_match_by_id, get_matches_for_user
from common.db.models.user import User
from common.db.session import get_db
from common.schemas.match import MatchOut

router = APIRouter()


@router.get("/", response_model=list[MatchOut])
async def get_my_matches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_matches_for_user(db, current_user.id)


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = await get_match_by_id(db, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if current_user.id not in (match.user1_id, match.user2_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your match")
    return match
