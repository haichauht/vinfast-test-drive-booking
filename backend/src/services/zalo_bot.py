"""Zalo Bot adapters for local polling and booking-access OTP delivery."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime, timedelta

import httpx

from src.database import Database
from src.services.booking.notifications import ProviderResult

_LINK_COMMAND = re.compile(r"^\s*LIENKET\s+((?:\+84|0)\d{9,10})\s*$", re.IGNORECASE)


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    return f"0{digits[2:]}" if digits.startswith("84") else digits


class ZaloBotClient:
    def __init__(self, *, token: str, api_base_url: str) -> None:
        self.token = token
        self.api_base_url = api_base_url.rstrip("/")

    def _url(self, method: str) -> str:
        return f"{self.api_base_url}/bot{self.token}/{method}"

    def send_text(self, chat_id: str, text: str) -> dict:
        response = httpx.post(self._url("sendMessage"), json={"chat_id": chat_id, "text": text}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(payload.get("description", "Zalo Bot rejected the message"))
        return payload

    async def get_updates(self, timeout_seconds: int, offset: int | None = None) -> list[dict]:
        request: dict[str, int] = {"timeout": timeout_seconds}
        if offset is not None:
            request["offset"] = offset
        async with httpx.AsyncClient(timeout=timeout_seconds + 10) as client:
            response = await client.post(self._url("getUpdates"), json=request)
        response.raise_for_status()
        payload = response.json()
        if payload.get("ok"):
            result = payload.get("result")
            return result if isinstance(result, list) else [result] if isinstance(result, dict) else []
        if payload.get("error_code") == 408:
            return []
        raise RuntimeError(payload.get("description", "Zalo getUpdates failed"))


class ZaloOtpSender:
    """Sends a booking OTP to the chat previously linked to its phone number."""

    def __init__(self, database: Database, client: ZaloBotClient) -> None:
        self.database = database
        self.client = client

    def is_linked(self, phone: str) -> bool:
        with self.database.connect() as connection:
            return connection.execute("SELECT 1 FROM zalo_identity_links WHERE phone=?", (normalize_phone(phone),)).fetchone() is not None

    def send(self, *, channel: str, destination: str, code: str, expires_in_seconds: int) -> ProviderResult:
        if channel != "zalo":
            raise ValueError("ZaloOtpSender only supports the zalo channel")
        phone = normalize_phone(destination)
        with self.database.connect() as connection:
            row = connection.execute("SELECT chat_id FROM zalo_identity_links WHERE phone=?", (phone,)).fetchone()
        if row is None:
            raise RuntimeError("Zalo account is not linked to this phone number")
        payload = self.client.send_text(row["chat_id"], f"Mã xác thực lịch lái thử VinFast: {code}. Mã có hiệu lực trong {expires_in_seconds // 60} phút.")
        return ProviderResult(
            provider="zalo_bot",
            channel="zalo",
            provider_status="sent",
            provider_message_id=str((payload.get("result") or {}).get("message_id") or ""),
            is_mock=False,
            sanitized_response={"ok": True},
        )

    def send_message(self, *, channel: str, destination: str, body: str) -> ProviderResult:
        if channel != "zalo":
            raise ValueError("ZaloOtpSender only supports the zalo channel")
        with self.database.connect() as connection:
            row = connection.execute("SELECT chat_id FROM zalo_identity_links WHERE phone=?", (normalize_phone(destination),)).fetchone()
        if row is None:
            raise RuntimeError("Zalo account is not linked to this phone number")
        payload = self.client.send_text(row["chat_id"], body)
        return ProviderResult(provider="zalo_bot", channel="zalo", provider_status="sent", provider_message_id=str((payload.get("result") or {}).get("message_id") or ""), is_mock=False, sanitized_response={"ok": True})


class ZaloPollingService:
    def __init__(self, database: Database, client: ZaloBotClient, timeout_seconds: int, retention_days: int = 30) -> None:
        self.database = database
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.retention_days = retention_days
        self._last_cleanup_at: datetime | None = None
        self._next_update_offset: int | None = None
        self.processed_message_ids: set[str] = set()
        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger.exception("Zalo polling failed; retrying shortly")
                await asyncio.sleep(3)

    async def poll_once(self) -> None:
        self._cleanup_processed_messages_if_due()
        for update in await self.client.get_updates(self.timeout_seconds, offset=self._next_update_offset):
            self._handle_update(update)
            update_id = _update_id(update)
            if update_id is not None:
                self._next_update_offset = update_id + 1

    def _cleanup_processed_messages_if_due(self) -> None:
        now = datetime.now(UTC)
        if self._last_cleanup_at and now - self._last_cleanup_at < timedelta(days=1):
            return
        cutoff = (now - timedelta(days=self.retention_days)).isoformat()
        with self.database.transaction(immediate=True) as connection:
            deleted = connection.execute(
                "DELETE FROM zalo_processed_messages WHERE processed_at<?", (cutoff,)
            ).rowcount
        self._last_cleanup_at = now
        if deleted:
            self.logger.info("Pruned %s expired Zalo processed-message records", deleted)

    def _handle_update(self, update: dict) -> None:
        message = update.get("message") or {}
        message_id = str(message.get("message_id") or "")
        if not message_id or message_id in self.processed_message_ids:
            return
        now = datetime.now(UTC).isoformat()
        with self.database.transaction(immediate=True) as connection:
            inserted = connection.execute(
                "INSERT INTO zalo_processed_messages(message_id,processed_at) VALUES(?,?) "
                "ON CONFLICT(message_id) DO NOTHING",
                (message_id, now),
            ).rowcount
        if not inserted:
            self.processed_message_ids.add(message_id)
            return
        self.processed_message_ids.add(message_id)
        text = str(message.get("text") or "")
        chat_id = str((message.get("chat") or {}).get("id") or "")
        match = _LINK_COMMAND.match(text)
        if not chat_id:
            return
        if not match:
            self.client.send_text(chat_id, "Để liên kết số điện thoại, hãy nhắn: LIENKET 09xxxxxxxx")
            return
        phone = normalize_phone(match.group(1))
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO zalo_identity_links(phone,chat_id,linked_at,updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(phone) DO UPDATE SET chat_id=excluded.chat_id,updated_at=excluded.updated_at",
                (phone, chat_id, now, now),
            )
        self.client.send_text(chat_id, f"Đã liên kết số {phone} với Zalo này. Bạn có thể nhận mã OTP để quản lý lịch lái thử trên website.")


def _update_id(update: dict) -> int | None:
    try:
        value = update.get("update_id")
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
