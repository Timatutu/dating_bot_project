from aiogram.enums import ButtonStyle
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_menu(likes_count: int = 0) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Моя анкета", style=ButtonStyle.PRIMARY),
                KeyboardButton(text="🔍 Смотреть анкеты", style=ButtonStyle.PRIMARY),
            ],
            [
                KeyboardButton(text="💎 Подписка", style=ButtonStyle.SUCCESS),
                KeyboardButton(text=f"❤️ Кто меня лайкнул ({likes_count})", style=ButtonStyle.DANGER),
            ],
        ],
        resize_keyboard=True,
    )


def profile_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile:edit", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🗑 Удалить анкету", callback_data="profile:delete", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="👁 Скрыть / Показать", callback_data="profile:toggle_visible")],
    ])


def create_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать анкету", callback_data="profile:create", style=ButtonStyle.SUCCESS)],
    ])


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender:male", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender:female", style=ButtonStyle.DANGER),
        ],
    ])


def skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip")],
    ])


def subscription_plans_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1 месяц — 1 звезда", callback_data="sub:month", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="⭐ 1 год — 1 звезда", callback_data="sub:year", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="💰 Оплата криптой (USDT)", callback_data="sub:crypto")],
    ])


def crypto_plans_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц — 5 USDT (ETH)", callback_data="crypto:eth:month")],
        [InlineKeyboardButton(text="1 год — 40 USDT (ETH)", callback_data="crypto:eth:year")],
        [InlineKeyboardButton(text="1 месяц — 5 USDT (SOL)", callback_data="crypto:sol:month")],
        [InlineKeyboardButton(text="1 год — 40 USDT (SOL)", callback_data="crypto:sol:year")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="crypto:back")],
    ])


def check_crypto_payment_kb(payment_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_crypto:{payment_id}")],
    ])


def confirm_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Всё верно", callback_data="profile:confirm", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text="🔄 Заново", callback_data="profile:restart", style=ButtonStyle.DANGER),
        ],
    ])
