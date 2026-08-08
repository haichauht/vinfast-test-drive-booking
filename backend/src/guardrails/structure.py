from __future__ import annotations

import json
import unicodedata
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_REMOVED_FORMAT_CHARACTERS = {
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\ufeff",  # BOM / zero-width no-break space
}


@dataclass(frozen=True, slots=True)
class PayloadLimits:
    max_bytes: int
    max_depth: int
    max_nodes: int
    max_string_chars: int


def normalize_text(value: str) -> str:
    """Normalize harmless Unicode differences and remove invisible controls."""
    normalized = unicodedata.normalize("NFC", value)
    cleaned: list[str] = []
    for character in normalized:
        if character in _REMOVED_FORMAT_CHARACTERS:
            continue
        category = unicodedata.category(character)
        if category == "Cc" and character not in {"\n", "\r", "\t"}:
            continue
        cleaned.append(character)
    return "".join(cleaned).strip()


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from iter_strings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from iter_strings(item)


def validate_payload(value: Any, limits: PayloadLimits) -> str | None:
    """Return a private rejection reason when a JSON-like payload is abusive."""
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    except (TypeError, ValueError):
        return "payload is not serializable"
    if len(encoded) > limits.max_bytes:
        return f"payload exceeds {limits.max_bytes} bytes"

    nodes = 0

    def walk(item: Any, depth: int) -> str | None:
        nonlocal nodes
        nodes += 1
        if nodes > limits.max_nodes:
            return f"payload exceeds {limits.max_nodes} nodes"
        if depth > limits.max_depth:
            return f"payload exceeds depth {limits.max_depth}"
        if isinstance(item, str) and len(item) > limits.max_string_chars:
            return f"payload string exceeds {limits.max_string_chars} characters"
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if len(str(key)) > 128:
                    return "payload contains an oversized key"
                violation = walk(nested, depth + 1)
                if violation:
                    return violation
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for nested in item:
                violation = walk(nested, depth + 1)
                if violation:
                    return violation
        return None

    return walk(value, 0)
