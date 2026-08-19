from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from src.services.llm import get_classifier_llm
from src.services.profile.models import SignalCandidate

logger = logging.getLogger("profile.extract")


class ExtractionResult(BaseModel):
    signals: list[SignalCandidate] = Field(default_factory=list)


class ProfileExtractor:
    async def extract(self, message: str, *, previous_agent_message: str = "", trace_id: str = "", conversation_id: str = "", profile_id: str = "") -> list[SignalCandidate]:
        logger.info("profile.extract.input trace_id=%s conversation_id=%s profile_id=%s message=%s previous_agent_message=%s", trace_id, conversation_id, profile_id, message, previous_agent_message)
        llm = get_classifier_llm()
        signals: list[SignalCandidate]
        if llm is None:
            signals = self._fallback(message)
        else:
            prompt = (
                "Extract only useful vehicle/test-drive personalization signals from the latest Vietnamese user message. "
                "Questions may imply interests or concerns. Use predefined categories fact, usage, experience, interest, concern, "
                "test_drive_goal, conversation_preference, likely_intent; use custom_intent for useful unmatched needs. "
                "Use known only for explicit facts, likely/possible for inference. Detect correction/retraction. "
                "Do not extract unrelated or sensitive authentication data. Avoid duplicate semantic signals.\n"
                f"Previous assistant message: {previous_agent_message}\nLatest user message: {message}"
            )
            try:
                # Intentionally bypass invoke_with_budget for the temporary profile-loop limit decision.
                result = await llm.with_structured_output(ExtractionResult).ainvoke(prompt)
                signals = result.signals
            except Exception:
                logger.exception("profile.extract.llm_failed trace_id=%s", trace_id)
                signals = self._fallback(message)
        logger.info("profile.extract.output trace_id=%s conversation_id=%s profile_id=%s signals=%s", trace_id, conversation_id, profile_id, [s.model_dump() for s in signals])
        return signals

    @staticmethod
    def _fallback(message: str) -> list[SignalCandidate]:
        text = message.casefold()
        result: list[SignalCandidate] = []
        rules = (
            (("sạc", "charging", "pin"), "interest", "charging", "Quan tâm đến pin/sạc"),
            (("250 km", "đường dài", "về quê", "cao tốc"), "usage", "long_trip", "Có nhu cầu đánh giá hành trình dài"),
            (("gia đình", "trẻ", "bé", "con"), "usage", "family", "Quan tâm sử dụng cho gia đình"),
            (("đỗ", "đậu", "hầm", "quay đầu"), "concern", "parking_maneuverability", "Quan tâm khả năng xoay trở/đỗ xe"),
            (("adas", "an toàn", "camera"), "interest", "safety_adas", "Quan tâm ADAS/an toàn"),
            (("chưa từng lái xe điện", "lần đầu lái xe điện"), "experience", "ev_experience", "Chưa có kinh nghiệm lái EV"),
        )
        for needles, category, key, description in rules:
            if any(needle in text for needle in needles):
                explicit = category == "experience" or bool(re.search(r"\b(tôi|mình|nhà|gia đình)\b", text))
                result.append(SignalCandidate(category=category, key=key, value=True, description=description, certainty="known" if explicit else "likely", confidence=0.9 if explicit else 0.7, source_type="explicit_user" if explicit else "implicit_user"))
        return result

