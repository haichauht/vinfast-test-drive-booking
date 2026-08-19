from __future__ import annotations

import json
import logging
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.enabled: bool = getattr(settings, "redis_enabled", False)
        self.url: str = getattr(settings, "redis_url", "")
        self._client: Any = None
        if self.enabled and self.url:
            try:
                import redis  # type: ignore[import-not-found,import-untyped]
                self._client = redis.from_url(self.url, decode_responses=True)
            except Exception as err:
                logger.warning("Failed to initialize Redis client (%s). Falling back to SQL/in-memory.", err)
                self._client = None

    def is_connected(self) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    @property
    def available(self) -> bool:
        return bool(self.enabled and self._client)

    def enqueue_reliable(
        self,
        queue_name: str,
        payload: dict[str, Any],
        *,
        dedupe_key: str,
        dedupe_ttl_seconds: int = 30,
    ) -> bool:
        """Atomically claim a short dedupe key and append a JSON job to Redis."""
        if not self._client:
            return False
        queue_key = f"queue:{queue_name}:pending"
        claim_key = f"queue:{queue_name}:dedupe:{dedupe_key}"
        encoded = json.dumps(payload, ensure_ascii=False)
        script = (
            "if redis.call('SET', KEYS[1], '1', 'NX', 'EX', ARGV[1]) then "
            "redis.call('LPUSH', KEYS[2], ARGV[2]); return 1 else return 0 end"
        )
        try:
            result = self._client.eval(
                script,
                2,
                claim_key,
                queue_key,
                str(dedupe_ttl_seconds),
                encoded,
            )
            # A duplicate is already queued or was processed recently, so it is
            # a successful no-op from the request path's perspective.
            return result in {0, 1}
        except Exception as err:
            logger.warning("Redis enqueue_reliable failed for %s: %s", queue_name, err)
            return False

    def reserve_reliable(self, queue_name: str, timeout_seconds: int = 1) -> str | None:
        """Move one job from pending to processing before returning it."""
        if not self._client:
            return None
        try:
            return self._client.brpoplpush(
                f"queue:{queue_name}:pending",
                f"queue:{queue_name}:processing",
                timeout=timeout_seconds,
            )
        except Exception as err:
            logger.warning("Redis reserve_reliable failed for %s: %s", queue_name, err)
            return None

    def ack_reliable(self, queue_name: str, encoded_payload: str) -> bool:
        if not self._client:
            return False
        try:
            self._client.lrem(f"queue:{queue_name}:processing", 1, encoded_payload)
            return True
        except Exception as err:
            logger.warning("Redis ack_reliable failed for %s: %s", queue_name, err)
            return False

    def retry_reliable(
        self,
        queue_name: str,
        encoded_payload: str,
        payload: dict[str, Any],
        *,
        dead_letter: bool,
    ) -> bool:
        if not self._client:
            return False
        destination = "dead" if dead_letter else "pending"
        try:
            pipeline = self._client.pipeline(transaction=True)
            pipeline.lrem(f"queue:{queue_name}:processing", 1, encoded_payload)
            pipeline.lpush(
                f"queue:{queue_name}:{destination}",
                json.dumps(payload, ensure_ascii=False),
            )
            pipeline.execute()
            return True
        except Exception as err:
            logger.warning("Redis retry_reliable failed for %s: %s", queue_name, err)
            return False

    def set_otp(self, key: str, code: str, ttl_seconds: int = 60) -> bool:
        if not self._client:
            return False
        try:
            self._client.setex(f"otp:{key}", ttl_seconds, code)
            return True
        except Exception as err:
            logger.warning("Redis set_otp failed: %s", err)
            return False

    def get_otp(self, key: str) -> str | None:
        if not self._client:
            return None
        try:
            return self._client.get(f"otp:{key}")
        except Exception as err:
            logger.warning("Redis get_otp failed: %s", err)
            return None

    def hold_slot(self, slot_id: str, booking_id: str, ttl_seconds: int = 120) -> bool:
        if not self._client:
            return False
        try:
            self._client.setex(f"hold_slot:{slot_id}", ttl_seconds, booking_id)
            return True
        except Exception as err:
            logger.warning("Redis hold_slot failed: %s", err)
            return False

    def is_slot_held(self, slot_id: str) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.exists(f"hold_slot:{slot_id}"))
        except Exception as err:
            logger.warning("Redis is_slot_held failed: %s", err)
            return False

    def release_slot_hold(self, slot_id: str) -> bool:
        if not self._client:
            return False
        try:
            self._client.delete(f"hold_slot:{slot_id}")
            return True
        except Exception as err:
            logger.warning("Redis release_slot_hold failed: %s", err)
            return False

    def set_cache(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        if not self._client:
            return False
        try:
            payload = json.dumps(value, ensure_ascii=False)
            self._client.setex(f"cache:{key}", ttl_seconds, payload)
            return True
        except Exception as err:
            logger.warning("Redis set_cache failed: %s", err)
            return False

    def get_cache(self, key: str) -> Any | None:
        if not self._client:
            return None
        try:
            raw = self._client.get(f"cache:{key}")
            return json.loads(raw) if raw else None
        except Exception as err:
            logger.warning("Redis get_cache failed: %s", err)
            return None


redis_client = RedisClient()
