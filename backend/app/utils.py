from __future__ import annotations

import re
from datetime import timedelta


def parse_iso8601_duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    # Handles the YouTube subset: P[nD]T[nH][nM][nS].
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?",
        value,
    )
    if not match:
        return None
    parts = {key: int(raw) if raw else 0 for key, raw in match.groupdict().items()}
    return int(timedelta(**parts).total_seconds())


def extract_channel_ref(value: str) -> tuple[str | None, str | None]:
    """Return (channel_id, handle) from a raw CSV value, URL, handle, or channel id."""
    cleaned = (value or "").strip()
    if not cleaned:
        return None, None
    if cleaned.startswith("UC") and len(cleaned) >= 20 and "/" not in cleaned:
        return cleaned, None
    if cleaned.startswith("@"):
        return None, cleaned

    handle_match = re.search(r"youtube\.com/@([^/?#]+)", cleaned)
    if handle_match:
        return None, f"@{handle_match.group(1)}"

    channel_match = re.search(r"youtube\.com/channel/(UC[^/?#]+)", cleaned)
    if channel_match:
        return channel_match.group(1), None

    # Last fallback: accept plain handle without @.
    if re.fullmatch(r"[A-Za-z0-9._-]{3,80}", cleaned):
        return None, f"@{cleaned}"
    return None, None
