from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.profile import main_menu
from common.db.crud.likes import get_likes_count
from common.db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, db: AsyncSession) -> None:
    likes_count = await get_likes_count(db, user.id)
    await message.answer(
        f"Привет, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Это бот для знакомств. Выбери действие:",
        reply_markup=main_menu(likes_count),
    )
