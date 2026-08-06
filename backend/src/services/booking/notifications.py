from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    channel: str
    provider_status: str
    provider_message_id: str | None
    is_mock: bool
    retryable: bool = False
    sanitized_response: dict | None = None


class MessagingProvider(Protocol):
    def send_message(self, *, channel: str, destination: str, body: str) -> ProviderResult: ...


class OtpSender(Protocol):
    def send(self, *, channel: str, destination: str, code: str, expires_in_seconds: int) -> ProviderResult: ...


@dataclass
class SentOtp:
    channel: str
    destination: str
    code: str
    expires_in_seconds: int


class InMemoryMessagingProvider:
    """Deterministic development adapter with an explicit mock contract."""

    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send_message(self, *, channel: str, destination: str, body: str) -> ProviderResult:
        message_id = f"mock_{uuid4().hex}"
        self.messages.append({"channel": channel, "destination": destination, "body": body, "id": message_id})
        return ProviderResult(
            provider=f"mock_{channel}",
            channel=channel,
            provider_status="mocked",
            provider_message_id=message_id,
            is_mock=True,
            sanitized_response={"accepted": True},
        )


class InMemoryOtpSender(InMemoryMessagingProvider):
    def __init__(self) -> None:
        super().__init__()
        self.sent: list[SentOtp] = []

    def send(self, *, channel: str, destination: str, code: str, expires_in_seconds: int) -> ProviderResult:
        self.sent.append(SentOtp(channel, destination, code, expires_in_seconds))
        return self.send_message(
            channel=channel,
            destination=destination,
            body=f"OTP có hiệu lực trong {expires_in_seconds} giây: {code}",
        )


def provider_result_dict(result: ProviderResult) -> dict:
    return asdict(result)
