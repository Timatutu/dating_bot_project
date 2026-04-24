from __future__ import annotations

import logging
import uuid
from contextlib import suppress

from aiogram import Bot
from aiogram.enums import ParseMode

from common.db.crud.users import get_user_by_id
from common.db.models.user import User
from common.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _contact_html(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    return f'<a href="tg://user?id={user.telegram_id}">Открыть чат</a>'


async def send_mutual_match_contacts(
    bot: Bot, user_a_id: uuid.UUID, user_b_id: uuid.UUID
) -> None:
    async with AsyncSessionLocal() as db:
        user_a = await get_user_by_id(db, user_a_id)
        user_b = await get_user_by_id(db, user_b_id)
    if user_a is None or user_b is None:
        return

    text_for_a = (
        "💌 <b>Взаимный лайк!</b> Можете написать друг другу. Контакт:\n"
        f"{_contact_html(user_b)}"
    )
    text_for_b = (
        "💌 <b>Взаимный лайк!</b> Можете написать друг другу. Контакт:\n"
        f"{_contact_html(user_a)}"
    )
    with suppress(Exception):
        await bot.send_message(
            user_a.telegram_id, text_for_a, parse_mode=ParseMode.HTML
        )
    with suppress(Exception):
        await bot.send_message(
            user_b.telegram_id, text_for_b, parse_mode=ParseMode.HTML
        )
    logger.info("mutual match contacts sent for %s <-> %s", user_a_id, user_b_id)
