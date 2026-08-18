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
