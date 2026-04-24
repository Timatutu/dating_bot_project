from __future__ import annotations

import asyncio
import random
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.crud.profiles import create_profile
from common.db.models.user import User
from common.db.session import AsyncSessionLocal
from common.services.rating_engine import recompute_rating_for_user

_BASE_TG = 5_000_000_000
_NAMES_M = [
    "Артём", "Михаил", "Иван", "Павел", "Сергей", "Алексей", "Дмитрий", "Никита",
    "Андрей", "Роман",
]
_NAMES_F = [
    "Анна", "Мария", "Елена", "Ольга", "София", "Полина", "Дарья", "Алиса",
    "Вероника", "Анастасия",
]
_TOTAL_PROFILES = 70
_CITIES = ["Москва", "Санкт-Петербург", "Чебоксары"]
_CITY_COORDS = {
    "Москва": (55.7558, 37.6176),
    "Санкт-Петербург": (59.9311, 30.3609),
    "Чебоксары": (56.1439, 47.2489),
}


async def _seed() -> None:
    random.seed(42)
    created = 0
    for i in range(_TOTAL_PROFILES):
        tid = _BASE_TG + i
        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(User).where(User.telegram_id == tid))
            if existing.scalar_one_or_none() is not None:
                continue
            new_user = User(telegram_id=tid, username=f"seed_user_{i}", is_active=True)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            gender = "male" if i < (_TOTAL_PROFILES // 2) else "female"
            name = (
                _NAMES_M[i % len(_NAMES_M)]
                if gender == "male"
                else _NAMES_F[i % len(_NAMES_F)]
            )
            age = 22 + (i % 12)
            city = random.choice(_CITIES)
            lat_base, lng_base = _CITY_COORDS[city]
            bio = (
                f"Тестовая анкета {i + 1}. Люблю путешествия, кофе и прогулки. Город: {city}."
            )
            photos = random.randint(0, 2)
            await create_profile(
                db,
                user_id=new_user.id,
                name=name,
                age=age,
                gender=gender,
                bio=bio,
                city=city,
                lat=lat_base + random.uniform(-0.08, 0.08),
                lng=lng_base + random.uniform(-0.08, 0.08),
                photos_count=photos,
            )
            created += 1

    async with AsyncSessionLocal() as session:
        batch = await session.execute(
            select(User).where(
                User.telegram_id >= _BASE_TG,
                User.telegram_id < _BASE_TG + _TOTAL_PROFILES,
            )
        )
        users = list(batch.scalars().all())

    for seed_user in users:
        async with AsyncSessionLocal() as session:
            await recompute_rating_for_user(session, seed_user.id)

    print(
        f"OK: {len(users)} users in seed range, {created} newly created, ratings recomputed."
    )


def main() -> None:
    asyncio.run(_seed())


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
