from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SignalCandidate(BaseModel):
    category: str
    key: str
    value: Any
    description: str = ""
    certainty: Literal["known", "likely", "possible"] = "possible"
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_type: Literal["explicit_user", "implicit_user", "trusted_domain"] = "implicit_user"
    operation: Literal["add", "strengthen", "weaken", "revise", "retract"] = "add"


class ProfileSnapshot(BaseModel):
    id: str
    state: Literal["anonymous", "trusted", "merged"]
    version: int = 1
    signals: list[dict[str, Any]] = Field(default_factory=list)

