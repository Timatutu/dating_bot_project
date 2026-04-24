from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from common.db.crud.likes import check_mutual_like, create_like, get_like
from common.db.crud.matches import get_or_create_match
from common.db.session import AsyncSessionLocal
from common.messaging.rabbit_publisher import publish_swipe_event
from common.services.rating_engine import recompute_rating_for_user


@dataclass(frozen=True)
class SwipeApplyResult:
    ok: bool
    already_same_action: bool
    created_match: bool


async def apply_like_or_skip(
    viewer_id: uuid.UUID,
    target_id: uuid.UUID,
    action: str,
) -> SwipeApplyResult:
    is_like = action == "like"
    created_match = False

    async with AsyncSessionLocal() as session:
        existing = await get_like(session, viewer_id, target_id)
        if existing is not None and existing.action == action:
            return SwipeApplyResult(
                ok=True, already_same_action=True, created_match=False
            )
        if existing is not None and existing.action != action:
            existing.action = action
            await session.commit()
        else:
            try:
                await create_like(session, viewer_id, target_id, action)
            except IntegrityError:
                return SwipeApplyResult(
                    ok=False, already_same_action=False, created_match=False
                )

    if is_like:
        async with AsyncSessionLocal() as session_mutual:
            if await check_mutual_like(session_mutual, viewer_id, target_id):
                await get_or_create_match(session_mutual, viewer_id, target_id)
                created_match = True

    async with AsyncSessionLocal() as session_viewer:
        await recompute_rating_for_user(session_viewer, viewer_id)
    async with AsyncSessionLocal() as session_target:
        await recompute_rating_for_user(session_target, target_id)

    await publish_swipe_event(
        action=action,
        from_user_id=viewer_id,
        to_user_id=target_id,
        created_match=created_match,
    )

    return SwipeApplyResult(
        ok=True, already_same_action=False, created_match=created_match
    )
