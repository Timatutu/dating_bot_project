import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | None:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, telegram_id: int, username: str | None = None) -> User:
    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user(db: AsyncSession, telegram_id: int, username: str | None = None) -> User:
    user = await get_user_by_telegram_id(db, telegram_id)
    if user is None:
        user = await create_user(db, telegram_id, username)
    elif user.username != username:
        user.username = username
        await db.commit()
        await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user
