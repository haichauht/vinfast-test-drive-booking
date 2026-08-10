import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return f"0{digits[2:]}" if digits.startswith("84") else digits


def row_to_dict(row) -> dict[str, Any] | None:
    return dict(row) if row else None
