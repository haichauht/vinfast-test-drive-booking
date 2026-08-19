from __future__ import annotations

from typing import Any

from src.services.profile.models import ProfileSnapshot


def build_profile_context(snapshot: ProfileSnapshot, message: str, *, limit: int = 12) -> dict[str, Any]:
    terms = set(message.casefold().split())
    ranked = sorted(snapshot.signals, key=lambda item: (sum(term in f"{item.get('key','')} {item.get('description','')}".casefold() for term in terms), float(item.get("confidence") or 0)), reverse=True)
    return {"profile_id": snapshot.id, "state": snapshot.state, "relevant_signals": ranked[:limit]}
