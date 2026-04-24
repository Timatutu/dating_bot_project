import logging
import uuid
from contextlib import suppress
from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from bot.keyboards.profile import main_menu
from bot.keyboards.swipe import feed_gender_kb, swipe_card_kb
from bot.services.match_notify import send_mutual_match_contacts
from bot.services.payment_client import PaymentClient
from bot.services.subscription_sync import sync_subscription_from_payment
from common.db.crud.likes import (
    get_pending_incoming_likes_count,
    get_sent_swipes_last_24h,
)
from common.db.crud.profiles import get_profile_by_user_id
from common.db.models.profile import Profile
from common.db.models.user import User
from common.db.session import AsyncSessionLocal
from common.formatting.profile_caption import format_profile_caption
from common.services.feed import get_next_candidate
from common.services.swipe_actions import apply_like_or_skip
from common.storage.s3 import download_photo

router = Router()
logger = logging.getLogger(__name__)
FREE_SWIPE_LIMIT_24H = 5


class SwipeFeed(StatesGroup):
    choosing_gender = State()
    choosing_city = State()
    card = State()


def _has_active_subscription(user: User) -> bool:
    ends = user.sub_expires_at
    if ends is None:
        return False
    ends_utc = ends if ends.tzinfo is not None else ends.replace(tzinfo=UTC)
    return ends_utc > datetime.now(UTC)


async def _is_swipe_limit_reached(user: User) -> bool:
    if _has_active_subscription(user):
        return False
    async with AsyncSessionLocal() as session:
        used = await get_sent_swipes_last_24h(session, user.id)
    return used >= FREE_SWIPE_LIMIT_24H


@router.message(F.text == "🔍 Смотреть анкеты")
async def browse_start(
    message: Message,
    user: User,
    state: FSMContext,
    payment_client: PaymentClient,
) -> None:
    current_state = await state.get_state()
    if current_state == SwipeFeed.card.state:
        await message.answer(
            "Сначала заверши просмотр: кнопки под карточкой или ⏹ Закончить.",
        )
        return
    if current_state == SwipeFeed.choosing_city.state:
        await message.answer("Сначала пришли название города одним сообщением.")
        return
    await sync_subscription_from_payment(payment_client, user.id)
    async with AsyncSessionLocal() as session:
        refreshed = await session.get(User, user.id)
    if refreshed is not None:
        user = refreshed

    if await _is_swipe_limit_reached(user):
        await state.clear()
        async with AsyncSessionLocal() as session:
            likes_n = await get_pending_incoming_likes_count(session, user.id)
        await message.answer(
            "Лимит бесплатных свайпов исчерпан: <b>5 за 24 часа</b>.\n"
            "💎 Подписка снимает это ограничение.",
            reply_markup=main_menu(likes_n),
        )
        return

    async with AsyncSessionLocal() as session:
        me = await get_profile_by_user_id(session, user.id)
    if me is None:
        await message.answer("Сначала создай анкету: 👤 Моя анкета → создать.")
        return

    await state.set_state(SwipeFeed.choosing_gender)
    await state.update_data(feed_preferred_gender=None, feed_city=None, candidate_user_id=None)
    await message.answer(
        "Кого показывать в ленте?",
        reply_markup=feed_gender_kb(),
    )


@router.callback_query(
    StateFilter(SwipeFeed.choosing_gender),
    F.data.in_({"feed:gender:male", "feed:gender:female"}),
)
async def feed_gender_chosen(
    callback: CallbackQuery, state: FSMContext
) -> None:
    gender = "male" if callback.data == "feed:gender:male" else "female"
    await state.update_data(feed_preferred_gender=gender)
    await state.set_state(SwipeFeed.choosing_city)
    text = (
        "В каком городе ищем? Напиши название одним сообщением "
        "(например: <b>Москва</b>)."
    )
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=None)
        except Exception:
            await callback.message.answer(text)
    await callback.answer()


@router.message(StateFilter(SwipeFeed.choosing_gender), F.text)
async def feed_gender_text_hint(message: Message) -> None:
    await message.answer("Выбери пол кнопками ниже: 👨 Мужчины или 👩 Женщины.")


@router.message(StateFilter(SwipeFeed.choosing_city), F.text)
async def feed_city_entered(message: Message, user: User, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if len(city) < 2:
        await message.answer("Название города слишком короткое. Напиши, например: Казань")
        return
    state_data = await state.get_data()
    preferred_gender = state_data.get("feed_preferred_gender")
    if preferred_gender not in ("male", "female"):
        await state.clear()
        await message.answer("Сессия сброшена. Нажми снова «🔍 Смотреть анкеты».")
        return

    await state.update_data(feed_city=city)
    async with AsyncSessionLocal() as session:
        next_profile = await get_next_candidate(
            session, user.id, preferred_gender=preferred_gender, city_query=city
        )
    if next_profile is None:
        await message.answer(
            "В этом городе пока нет подходящих анкет (или в базе пусто). "
            "Напиши <b>другое название города</b> одним сообщением "
            "(проверь написание; для сидов подходят, например: Москва, Казань). "
            "Или загрузи сиды: <code>python -m workers.seed_test_profiles</code>.",
        )
        return

    await state.set_state(SwipeFeed.card)
    await state.update_data(candidate_user_id=str(next_profile.user_id))
    await _send_card_to_message(message, next_profile)


@router.message(StateFilter(SwipeFeed.card), F.text)
async def block_text_in_swipe(message: Message) -> None:
    await message.answer("Используй кнопки под карточкой: ❤️ / 👎 / ⏹.")


@router.callback_query(SwipeFeed.card, F.data == "swipe:like")
@router.callback_query(SwipeFeed.card, F.data == "swipe:skip")
async def on_swipe_action(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    payment_client: PaymentClient,
) -> None:
    fsm_data = await state.get_data()
    raw = fsm_data.get("candidate_user_id")
    if not raw:
        await callback.answer("Начни ленту: «🔍 Смотреть анкеты»", show_alert=True)
        return
    target = uuid.UUID(raw)
    is_like = callback.data == "swipe:like"
    action = "like" if is_like else "skip"
    await sync_subscription_from_payment(payment_client, user.id)
    async with AsyncSessionLocal() as session:
        refreshed = await session.get(User, user.id)
    if refreshed is not None:
        user = refreshed

    if await _is_swipe_limit_reached(user):
        await state.clear()
        await callback.answer("Лимит свайпов исчерпан", show_alert=True)
        if callback.message:
            async with AsyncSessionLocal() as session:
                likes_n = await get_pending_incoming_likes_count(session, user.id)
            await callback.message.answer(
                "Лимит бесплатных свайпов исчерпан: <b>5 за 24 часа</b>.\n"
                "💎 Подписка снимает ограничение.",
                reply_markup=main_menu(likes_n),
            )
        return
    result = await apply_like_or_skip(user.id, target, action)
    if not result.ok:
        await callback.answer("Уже оценено.", show_alert=True)
        return
    if result.already_same_action:
        await callback.answer("Уже отмечено.", show_alert=True)
        return

    if is_like:
        await callback.answer(
            "Взаимный мэтч! 💌" if result.created_match else "Лайк ❤️",
            show_alert=result.created_match,
        )
        if result.created_match:
            await send_mutual_match_contacts(callback.bot, user.id, target)
    else:
        await callback.answer("Пропуск")

    if not callback.message:
        return
    chat = callback.message.chat
    bot = callback.bot
    with suppress(Exception):
        await callback.message.delete()

    next_profile = await _load_next_with_photos(state, user.id)
    if next_profile is None:
        await state.clear()
        async with AsyncSessionLocal() as session_likes:
            likes_n = await get_pending_incoming_likes_count(session_likes, user.id)
        await bot.send_message(
            chat.id,
            "Пока больше нет анкет. Зайди позже! 🔜",
            reply_markup=main_menu(likes_n),
        )
        return

    await state.update_data(candidate_user_id=str(next_profile.user_id))
    await _send_card_to_chat(bot, chat.id, next_profile)


@router.callback_query(SwipeFeed.card, F.data == "swipe:stop")
async def swipe_stop(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    await state.clear()
    async with AsyncSessionLocal() as session:
        likes_n = await get_pending_incoming_likes_count(session, user.id)
    with suppress(Exception):
        if callback.message:
            await callback.message.delete()
    if callback.message:
        await callback.message.answer("Лента остановлена.", reply_markup=main_menu(likes_n))
    await callback.answer()


async def _load_next_with_photos(state: FSMContext, viewer: uuid.UUID) -> Profile | None:
    state_data = await state.get_data()
    preferred_gender = state_data.get("feed_preferred_gender")
    search_city = state_data.get("feed_city")
    if preferred_gender not in ("male", "female") or not search_city:
        return None
    async with AsyncSessionLocal() as session:
        return await get_next_candidate(
            session,
            viewer,
            preferred_gender=preferred_gender,
            city_query=search_city,
        )


async def _send_card_to_message(message: Message, profile: Profile) -> None:
    cap = f"<b>Анкета</b>\n\n{format_profile_caption(profile)}"
    for photo in profile.photos or []:
        with suppress(Exception):
            data = await download_photo(photo.s3_key)
            await message.answer_photo(
                BufferedInputFile(data, filename="p.jpg"),
                caption=cap,
                reply_markup=swipe_card_kb(),
            )
            return
    await message.answer(cap, reply_markup=swipe_card_kb())


async def _send_card_to_chat(bot: Bot, chat_id: int, profile: Profile) -> None:
    cap = f"<b>Анкета</b>\n\n{format_profile_caption(profile)}"
    for photo in profile.photos or []:
        with suppress(Exception):
            data = await download_photo(photo.s3_key)
            await bot.send_photo(
                chat_id,
                BufferedInputFile(data, filename="p.jpg"),
                caption=cap,
                reply_markup=swipe_card_kb(),
            )
            return
    await bot.send_message(chat_id, cap, reply_markup=swipe_card_kb())
