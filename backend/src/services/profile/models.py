from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class SignalCandidate(BaseModel):
    category: str
    key: str
    value: Any
    description: str = ""
    certainty: Literal["known", "likely", "possible"] = "possible"
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_type: Literal["explicit_user", "implicit_user", "trusted_domain"] = "implicit_user"
    operation: Literal["add", "strengthen", "weaken", "revise", "retract"] = "add"


class ProfileSignalCandidate(SignalCandidate):
    subject: Literal["self", "third_party"] = "self"


class BookingSignalCandidate(BaseModel):
    """A booking-scoped fact. Core keys are intentionally typed; custom.* is extensible."""
    category: str
    key: str
    value: Any
    description: str = ""
    subject: Literal["booking", "booker", "driver", "group"]
    certainty: Literal["known", "likely", "possible"] = "possible"
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_type: Literal["explicit_user", "implicit_user", "trusted_domain"] = "implicit_user"
    operation: Literal["add", "strengthen", "weaken", "revise", "retract"] = "add"

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        key = str(data.get("key") or "")
        if key.endswith(("_evaluation_involvement", "_purchase_involvement")) and isinstance(
            data.get("value"), bool
        ):
            normalized["value"] = "high" if data["value"] else "none"
        if key == "additional_guest_context" and isinstance(data.get("value"), str):
            normalized["value"] = [data["value"]]
        return normalized

    def model_post_init(self, __context: Any) -> None:
        bool_keys = {"booker_attending", "driver_attending", "booker_will_drive", "driver_will_drive"}
        involvement = {"booker_evaluation_involvement", "driver_evaluation_involvement", "booker_purchase_involvement", "driver_purchase_involvement"}
        expected_subject = "booker" if self.key.startswith("booker_") else "driver" if self.key.startswith("driver_") else "group" if self.key.startswith("additional_guest_") else None
        if expected_subject and self.subject != expected_subject:
            raise ValueError(f"{self.key} must use subject={expected_subject}")
        if self.key in bool_keys and not isinstance(self.value, bool):
            raise ValueError(f"{self.key} must be boolean")
        if self.key == "additional_guest_count" and (not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 0):
            raise ValueError("additional_guest_count must be an integer >= 0")
        if self.key == "additional_guest_context" and not isinstance(self.value, list):
            raise ValueError("additional_guest_context must be a list")
        if self.key in involvement and self.value not in {"none", "low", "medium", "high"}:
            raise ValueError(f"{self.key} must be none, low, medium, or high")
        if self.key not in bool_keys | involvement | {"additional_guest_count", "additional_guest_context"} and not self.key.startswith("custom."):
            raise ValueError("booking signal key must be a registered core key or start with custom.")


class ProfileSnapshot(BaseModel):
    id: str
    state: Literal["anonymous", "trusted", "merged"]
    version: int = 1
    signals: list[dict[str, Any]] = Field(default_factory=list)
