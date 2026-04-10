from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text == "🔍 Смотреть анкеты")
async def browse_profiles(message: Message) -> None:
    await message.answer("Скоро тут будет свайп-лента 🔜")
