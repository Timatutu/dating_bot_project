from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def feed_gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужчины", callback_data="feed:gender:male"),
                InlineKeyboardButton(text="👩 Женщины", callback_data="feed:gender:female"),
            ],
        ],
    )


def inbound_liker_kb(liker_user_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ Лайк", callback_data=f"inbound:like:{liker_user_id}"
                ),
                InlineKeyboardButton(
                    text="👎 Не моё", callback_data=f"inbound:skip:{liker_user_id}"
                ),
            ],
        ],
    )


def swipe_card_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Лайк", callback_data="swipe:like"),
                InlineKeyboardButton(text="👎 Пропуск", callback_data="swipe:skip"),
            ],
            [InlineKeyboardButton(text="⏹ Закончить", callback_data="swipe:stop")],
        ]
    )
