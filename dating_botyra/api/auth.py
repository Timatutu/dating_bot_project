import hashlib
import hmac
import uuid
from urllib.parse import parse_qsl, unquote

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.config import settings
from common.db.crud.users import get_or_create_user
from common.db.models.user import User
from common.db.session import AsyncSession, get_db

_tg_header = APIKeyHeader(name="X-Telegram-Init-Data", auto_error=True)


def _verify_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(unquote(init_data), keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    return parsed


async def get_current_user(
    init_data: str = Security(_tg_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    data = _verify_init_data(init_data)

    import json
    user_data = json.loads(data.get("user", "{}"))
    telegram_id = user_data.get("id")
    username = user_data.get("username")

    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No user in initData")

    user = await get_or_create_user(db, telegram_id=int(telegram_id), username=username)
    return user
