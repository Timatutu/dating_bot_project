import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.profile import (
    confirm_profile_kb,
    create_profile_kb,
    gender_kb,
    main_menu,
    profile_actions,
    skip_kb,
)
from common.db.crud.likes import get_likes_count
from common.db.crud.profiles import create_profile, delete_profile, get_profile_by_user_id, update_profile
from common.db.models.photo import Photo
from common.db.models.user import User
from common.storage.s3 import download_photo, upload_photo

router = Router()



class ProfileCreate(StatesGroup):
    gender = State()
    age = State()
    name = State()
    city = State()
    bio = State()
    photo = State()
    confirm = State()



@router.message(F.text == "👤 Моя анкета")
async def my_profile(
    message: Message, user: User, db: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    profile = await get_profile_by_user_id(db, user.id)

    if profile is None:
        await message.answer(
            "У тебя пока нет анкеты.\nСоздай её, чтобы тебя видели другие! 👇",
            reply_markup=create_profile_kb(),
        )
        return

    if profile.photos:
        primary = next((p for p in profile.photos if p.is_primary), profile.photos[0])
        try:
            photo_bytes = await download_photo(primary.s3_key)
            photo_file = BufferedInputFile(photo_bytes, filename="photo.jpg")
            await message.answer_photo(
                photo=photo_file,
                caption=_profile_text(profile),
                reply_markup=profile_actions(),
            )
        except Exception:
            await message.answer(_profile_text(profile), reply_markup=profile_actions())
        return

    await message.answer(_profile_text(profile), reply_markup=profile_actions())


def _profile_text(profile) -> str:
    gender_map = {"male": "👨 Мужской", "female": "👩 Женский"}
    lines = [
        f"<b>{profile.name}</b>, {profile.age} лет",
        f"Пол: {gender_map.get(profile.gender, profile.gender)}",
    ]
    if profile.city:
        lines.append(f"📍 {profile.city}")
    if profile.bio:
        lines.append(f"\n{profile.bio}")
    visibility = "👁 Анкета видна" if profile.is_visible else "🙈 Анкета скрыта"
    lines.append(f"\n{visibility}")
    return "\n".join(lines)



@router.callback_query(F.data == "profile:toggle_visible")
async def toggle_visible(callback: CallbackQuery, user: User, db: AsyncSession) -> None:
    profile = await get_profile_by_user_id(db, user.id)
    if profile:
        await update_profile(db, profile, is_visible=not profile.is_visible)
        state_text = "видна" if not profile.is_visible else "скрыта"
        await callback.answer(f"Анкета теперь {state_text}")
        await callback.message.edit_reply_markup(reply_markup=profile_actions())


@router.callback_query(F.data == "profile:delete")
async def delete_profile_handler(callback: CallbackQuery, user: User, db: AsyncSession) -> None:
    profile = await get_profile_by_user_id(db, user.id)
    if profile:
        await delete_profile(db, profile)
    likes_count = await get_likes_count(db, user.id)
    await callback.message.answer("Анкета удалена.", reply_markup=main_menu(likes_count))
    await callback.message.delete()
    await callback.answer()



@router.callback_query(F.data == "profile:create")
async def start_create(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer("Выбери свой пол 👇", reply_markup=gender_kb())
    await state.set_state(ProfileCreate.gender)
    await callback.answer()


@router.callback_query(F.data == "profile:restart")
async def restart_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Начнём заново. Выбери свой пол 👇", reply_markup=gender_kb())
    await state.set_state(ProfileCreate.gender)
    await callback.answer()


@router.callback_query(ProfileCreate.gender, F.data.startswith("gender:"))
async def step_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await callback.message.answer("Сколько тебе лет?")
    await state.set_state(ProfileCreate.age)
    await callback.answer()


@router.message(ProfileCreate.age)
async def step_age(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("Введи своё возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Как тебя зовут? Введи имя, которое увидят другие 👤")
    await state.set_state(ProfileCreate.name)


@router.message(ProfileCreate.name)
async def step_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name or len(name) > 64:
        await message.answer("Введи имя (не более 64 символов).")
        return
    await state.update_data(name=name)
    await message.answer("В каком городе ты живёшь?")
    await state.set_state(ProfileCreate.city)


@router.message(ProfileCreate.city)
async def step_city(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if not city:
        await message.answer("Введи название города.")
        return
    await state.update_data(city=city)
    await message.answer(
        "Расскажи немного о себе 📝\n(или пропусти)",
        reply_markup=skip_kb(),
    )
    await state.set_state(ProfileCreate.bio)


@router.message(ProfileCreate.bio)
async def step_bio(message: Message, state: FSMContext) -> None:
    bio = (message.text or "").strip() or None
    await state.update_data(bio=bio)
    await message.answer(
        "Отправь своё фото 📸\n(или пропусти)",
        reply_markup=skip_kb(),
    )
    await state.set_state(ProfileCreate.photo)


@router.callback_query(ProfileCreate.bio, F.data == "skip")
async def skip_bio(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(bio=None)
    await callback.message.answer(
        "Отправь своё фото 📸\n(или пропусти)",
        reply_markup=skip_kb(),
    )
    await state.set_state(ProfileCreate.photo)
    await callback.answer()


@router.message(ProfileCreate.photo, F.photo)
async def step_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_io = await message.bot.download_file(file.file_path)
    content = file_io.read() if hasattr(file_io, "read") else bytes(file_io)

    try:
        s3_key = await upload_photo(content)
        await state.update_data(s3_key=s3_key)
    except Exception as e:
        logging.getLogger(__name__).warning("Фото не загружено в S3: %s", e)
        await state.update_data(s3_key=None)
        await message.answer("⚠️ Не удалось сохранить фото, продолжаем без него.")

    await _show_confirm(message, state)


@router.callback_query(ProfileCreate.photo, F.data == "skip")
async def skip_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(s3_key=None)
    await _show_confirm(callback.message, state)
    await callback.answer()


async def _show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    gender_map = {"male": "👨 Мужской", "female": "👩 Женский"}
    text = (
        "<b>Проверь свою анкету:</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Пол: {gender_map.get(data['gender'], data['gender'])}\n"
        f"Возраст: {data['age']}\n"
        f"Город: {data['city']}\n"
        f"О себе: {data.get('bio') or '—'}\n"
        f"Фото: {'✅' if data.get('s3_key') else '—'}"
    )
    await message.answer(text, reply_markup=confirm_profile_kb())
    await state.set_state(ProfileCreate.confirm)


@router.callback_query(ProfileCreate.confirm, F.data == "profile:confirm")
async def confirm_create(callback: CallbackQuery, state: FSMContext, user: User, db: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()

    profile = await create_profile(
        db,
        user_id=user.id,
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        bio=data.get("bio"),
        city=data["city"],
    )

    if data.get("s3_key"):
        photo_obj = Photo(
            profile_id=profile.id,
            s3_key=data["s3_key"],
            is_primary=True,
            position=0,
        )
        db.add(photo_obj)
        profile.photos_count = 1
        await db.commit()

    likes_count = await get_likes_count(db, user.id)
    await callback.message.answer(
        "Анкета создана! Теперь тебя видят другие.",
        reply_markup=main_menu(likes_count),
    )
    await callback.answer()
