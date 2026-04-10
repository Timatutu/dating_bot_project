from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from common.db.crud.users import get_or_create_user
from common.db.session import AsyncSessionLocal


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        async with AsyncSessionLocal() as db:
            data["db"] = db

            if tg_user:
                user = await get_or_create_user(
                    db,
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                )
                data["user"] = user
            else:
                data["user"] = None

            return await handler(event, data)
