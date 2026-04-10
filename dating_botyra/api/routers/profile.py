from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from common.db.crud.profiles import (
    create_profile,
    delete_profile,
    get_profile_by_user_id,
    update_profile,
)
from common.db.models.user import User
from common.db.session import get_db
from common.schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await get_profile_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile_endpoint(
    data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await get_profile_by_user_id(db, current_user.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")
    return await create_profile(db, user_id=current_user.id, **data.model_dump())


@router.patch("/me", response_model=ProfileOut)
async def update_profile_endpoint(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await get_profile_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return await update_profile(db, profile, **data.model_dump(exclude_none=True))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await get_profile_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await delete_profile(db, profile)
