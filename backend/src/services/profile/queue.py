from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import unicodedata
from typing import Any

from src.database.redis_client import RedisClient
from src.services.profile.extractor import ProfileExtractor
from src.services.profile.service import ProfileService

logger = logging.getLogger("profile.queue")

QUEUE_NAME = "profile-extraction-v1"
MAX_RETRIES = 3
_EMAIL_ONLY = re.compile(r"^\s*[^\s@]+@[^\s@]+\.[^\s@]+\s*$")
_BOOKING_CODE_ONLY = re.compile(r"^\s*(?:BK|BOOKING)[-_A-Z0-9]{4,}\s*$", re.IGNORECASE)
_OTP_ONLY = re.compile(r"^\s*\d{4,8}\s*$")
_LOW_VALUE_MESSAGES = {
    "xin chao",
    "chao",
    "hello",
    "hi",
    "cam on",
    "thank you",
    "thanks",
    "tam biet",
    "bye",
}
_CONFIRMATION_MARKERS = (
    "ok",
    "okay",
    "dat di",
    "chot di",
    "xac nhan",
    "dong y",
    "lay lich nay",
)


class ProfileExtractionQueue:
    def __init__(
        self,
        redis: RedisClient,
        extractor: ProfileExtractor,
        profiles: ProfileService,
    ) -> None:
        self.redis = redis
        self.extractor = extractor
        self.profiles = profiles
        self._worker_task: asyncio.Task[None] | None = None

    @staticmethod
    def eligibility(
        message: str,
        *,
        requested_action: str = "",
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        decomposed = unicodedata.normalize("NFKD", message.casefold())
        normalized = " ".join(
            "".join(char for char in decomposed if not unicodedata.combining(char)).split()
        )
        if not normalized:
            return False, "empty"
        # Explicit confirmations and short messages are always eligible. Never
        # use length alone as a reason to skip profile extraction.
        if any(marker in normalized for marker in _CONFIRMATION_MARKERS):
            return True, "confirmation"
        if normalized in _LOW_VALUE_MESSAGES:
            return False, "social_only"
        if _EMAIL_ONLY.fullmatch(message):
            return False, "email_only"
        if _BOOKING_CODE_ONLY.fullmatch(message):
            return False, "booking_code_only"
        verification_context = "verify" in requested_action.casefold() or any(
            token in str((context or {}).get(key, "")).casefold()
            for key in ("stage", "phase", "purpose")
            for token in ("otp", "verify", "verification")
        )
        if verification_context and _OTP_ONLY.fullmatch(message):
            return False, "otp_only"
        return True, "potential_signal"

    async def enqueue(
        self,
        *,
        profile_id: str,
        conversation_id: str,
        trace_id: str,
        message: str,
        previous_agent_message: str,
        requested_action: str = "",
        context: dict[str, Any] | None = None,
    ) -> bool:
        eligible, reason = self.eligibility(
            message,
            requested_action=requested_action,
            context=context,
        )
        if not eligible:
            logger.info(
                "profile.queue.skipped trace_id=%s conversation_id=%s profile_id=%s reason=%s",
                trace_id,
                conversation_id,
                profile_id,
                reason,
            )
            return True
        if not self.redis.available:
            logger.warning(
                "profile.queue.unavailable trace_id=%s conversation_id=%s profile_id=%s",
                trace_id,
                conversation_id,
                profile_id,
            )
            return False

        dedupe_material = f"{conversation_id}\0{message}".encode()
        dedupe_key = hashlib.sha256(dedupe_material).hexdigest()
        payload = {
            "profile_id": profile_id,
            "conversation_id": conversation_id,
            "trace_id": trace_id,
            "message": message,
            "previous_agent_message": previous_agent_message,
            "retry_count": 0,
        }
        try:
            queued = await asyncio.wait_for(
                asyncio.to_thread(
                    self.redis.enqueue_reliable,
                    QUEUE_NAME,
                    payload,
                    dedupe_key=dedupe_key,
                ),
                timeout=0.5,
            )
        except TimeoutError:
            queued = False
            logger.warning(
                "profile.queue.enqueue_timeout trace_id=%s conversation_id=%s profile_id=%s",
                trace_id,
                conversation_id,
                profile_id,
            )
        if queued:
            self.start()
            logger.info(
                "profile.queue.enqueued trace_id=%s conversation_id=%s profile_id=%s reason=%s",
                trace_id,
                conversation_id,
                profile_id,
                reason,
            )
        else:
            logger.warning(
                "profile.queue.enqueue_failed trace_id=%s conversation_id=%s profile_id=%s",
                trace_id,
                conversation_id,
                profile_id,
            )
        return queued

    def start(self) -> None:
        if not self.redis.available:
            return
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._run(), name="profile-extraction-worker")
            logger.info("profile.queue.worker_started queue=%s", QUEUE_NAME)

    async def stop(self) -> None:
        task = self._worker_task
        self._worker_task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("profile.queue.worker_stopped queue=%s", QUEUE_NAME)

    async def _run(self) -> None:
        while True:
            try:
                encoded = await asyncio.to_thread(self.redis.reserve_reliable, QUEUE_NAME, 1)
                if not encoded:
                    await asyncio.sleep(0)
                    continue
                await self._process(encoded)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("profile.queue.worker_error queue=%s", QUEUE_NAME)
                await asyncio.sleep(1)

    async def _process(self, encoded: str) -> None:
        try:
            payload = json.loads(encoded)
            candidates = await self.extractor.extract(
                str(payload["message"]),
                previous_agent_message=str(payload.get("previous_agent_message") or ""),
                trace_id=str(payload.get("trace_id") or ""),
                conversation_id=str(payload["conversation_id"]),
                profile_id=str(payload["profile_id"]),
            )
            if candidates:
                await asyncio.to_thread(
                    self.profiles.apply,
                    str(payload["profile_id"]),
                    candidates,
                    source_ref=str(payload["conversation_id"]),
                    trace_id=str(payload.get("trace_id") or ""),
                )
            await asyncio.to_thread(self.redis.ack_reliable, QUEUE_NAME, encoded)
            logger.info(
                "profile.queue.completed trace_id=%s conversation_id=%s profile_id=%s signals=%s",
                payload.get("trace_id"),
                payload.get("conversation_id"),
                payload.get("profile_id"),
                len(candidates),
            )
        except Exception:
            try:
                payload = json.loads(encoded)
            except (TypeError, json.JSONDecodeError):
                logger.exception("profile.queue.invalid_payload queue=%s", QUEUE_NAME)
                await asyncio.to_thread(self.redis.ack_reliable, QUEUE_NAME, encoded)
                return
            logger.exception(
                "profile.queue.processing_failed queue=%s trace_id=%s conversation_id=%s profile_id=%s",
                QUEUE_NAME,
                payload.get("trace_id"),
                payload.get("conversation_id"),
                payload.get("profile_id"),
            )
            retry_count = int(payload.get("retry_count") or 0) + 1
            payload["retry_count"] = retry_count
            await asyncio.to_thread(
                self.redis.retry_reliable,
                QUEUE_NAME,
                encoded,
                payload,
                dead_letter=retry_count >= MAX_RETRIES,
            )
            if retry_count < MAX_RETRIES:
                await asyncio.sleep(min(2**retry_count, 8))
