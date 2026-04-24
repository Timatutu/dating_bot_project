import uuid
from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.profile import main_menu
from bot.keyboards.swipe import inbound_liker_kb
from bot.services.match_notify import send_mutual_match_contacts
from common.db.crud.likes import (
    get_pending_incoming_likes_count,
    list_pending_incoming_liker_ids,
)
from common.db.crud.profiles import get_profile_by_user_id
from common.db.models.user import User
from common.formatting.profile_caption import format_profile_caption
from common.services.swipe_actions import apply_like_or_skip
from common.storage.s3 import download_photo

router = Router()


@router.message(F.text.regexp(r"^❤️ Кто меня лайкнул"))
async def who_liked_me(
    message: Message, user: User, db: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    likes_count = await get_pending_incoming_likes_count(db, user.id)
    if likes_count == 0:
        await message.answer(
            "Тебя ещё никто не лайкнул 😔",
            reply_markup=main_menu(0),
        )
        return

    liker_ids = await list_pending_incoming_liker_ids(db, user.id, limit=20)
    await message.answer(
        f"❤️ <b>Тебя лайкнули {likes_count} раз(а)</b> — вот кто (до 20, новые сверху). "
        f"Нажми <b>Лайк</b>, если тоже интересно, или <b>Не моё</b>.\n"
        f"(если анкету удалили, человек не покажется)",
    )
    for liker_id in liker_ids:
        profile = await get_profile_by_user_id(db, liker_id)
        if profile is None:
            continue
        cap = f"<b>Анкета</b>\n\n{format_profile_caption(profile)}"
        liker_id_str = str(liker_id)
        reply = inbound_liker_kb(liker_id_str)
        sent_photo = False
        for photo in profile.photos or []:
            with suppress(Exception):
                data = await download_photo(photo.s3_key)
                await message.answer_photo(
                    BufferedInputFile(data, filename="p.jpg"),
                    caption=cap,
                    reply_markup=reply,
                )
                sent_photo = True
                break
        if not sent_photo:
            await message.answer(cap, reply_markup=reply)

    await message.answer(
        "👆 Ответь кнопками под карточками. При <b>взаимном лайке</b> вы оба "
        "получите контакты (юзернейм или ссылку).",
        reply_markup=main_menu(likes_count),
    )


@router.callback_query(
    (F.data.startswith("inbound:like:")) | (F.data.startswith("inbound:skip:"))
)
async def inbound_liker_action(
    callback: CallbackQuery, user: User, bot: Bot, db: AsyncSession
) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    try:
        _, action_raw, target_raw = callback.data.split(":", 2)
    except ValueError:
        await callback.answer("Ошибка", show_alert=True)
        return
    action = "like" if action_raw == "like" else "skip"
    try:
        target_id = uuid.UUID(target_raw)
    except ValueError:
        await callback.answer("Ошибка", show_alert=True)
        return
    if target_id == user.id:
        await callback.answer("Это твой id", show_alert=True)
        return

    result = await apply_like_or_skip(user.id, target_id, action)
    if not result.ok:
        await callback.answer("Уже оценено.", show_alert=True)
        return
    if result.already_same_action:
        await callback.answer("Уже отмечено.", show_alert=True)
        return

    if action == "like":
        await callback.answer(
            "Взаимный мэтч! 💌" if result.created_match else "Лайк записан ❤️",
            show_alert=result.created_match,
        )
        if result.created_match:
            await send_mutual_match_contacts(bot, user.id, target_id)
    else:
        await callback.answer("Пропущено")

    with suppress(Exception):
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)

    likes_count = await get_pending_incoming_likes_count(db, user.id)
    if callback.message:
        await callback.message.answer(
            f"Осталось новых лайков: <b>{likes_count}</b>",
            reply_markup=main_menu(likes_count),
        )
