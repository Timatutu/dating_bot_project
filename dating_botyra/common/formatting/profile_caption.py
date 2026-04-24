from __future__ import annotations

from common.db.models.profile import Profile


def text_limit(text: str, max_len: int = 200) -> str:
    trimmed = text.strip() if text else ""
    if len(trimmed) > max_len:
        return trimmed[: max_len - 1] + "…"
    return trimmed


def format_profile_caption(profile: Profile) -> str:
    gmap = {"male": "муж", "female": "жен", "other": "друг(ая)"}
    lines = [f"{profile.name}, {profile.age} — {gmap.get(profile.gender, profile.gender)}"]
    if profile.city:
        lines.append(f"📍 {profile.city}")
    if profile.bio:
        lines.append(f"\n{text_limit(profile.bio, 500)}")
    return "\n".join(lines)
