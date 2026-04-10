from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.profile import main_menu
from common.db.crud.likes import get_likes_count
from common.db.models.user import User

router = Router()


@router.message(F.text.regexp(r"^❤️ Кто меня лайкнул"))
async def who_liked_me(message: Message, user: User, db: AsyncSession) -> None:
    likes_count = await get_likes_count(db, user.id)
    if likes_count == 0:
        text = "Тебя ещё никто не лайкнул 😔"
    else:
        text = f"Тебя лайкнули <b>{likes_count}</b> раз(а) ❤️"
    await message.answer(text, reply_markup=main_menu(likes_count))
