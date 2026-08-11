import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def parse_utc(value: str | datetime) -> datetime:
    """Parse a persisted timestamp into one UTC-aware datetime.

    Legacy CSV rows without an offset are interpreted as UTC. New imports are
    normalized back to an explicit ``+00:00`` representation before storage.
    """
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def normalize_timestamp(value: str | datetime) -> str:
    """Return the canonical persisted representation for an instant in time."""
    return iso(parse_utc(value))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return f"0{digits[2:]}" if digits.startswith("84") else digits


def row_to_dict(row) -> dict[str, Any] | None:
    return dict(row) if row else None
