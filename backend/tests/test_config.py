import pytest
from pydantic import ValidationError
from src.config import Settings


def test_production_requires_a_strong_otp_secret():
    with pytest.raises(ValidationError, match="BOOKING_ACCESS_OTP_SECRET"):
        Settings(app_env="production", booking_access_otp_secret="too-short")

    settings = Settings(
        app_env="production",
        booking_access_otp_secret="a" * 32,
        conversation_signing_secret="b" * 32,
    )

    assert settings.booking_access_otp_secret == "a" * 32


def test_production_cannot_disable_guardrails():
    with pytest.raises(ValidationError, match="GUARDRAILS_ENABLED"):
        Settings(
            app_env="production",
            booking_access_otp_secret="a" * 32,
            conversation_signing_secret="b" * 32,
            guardrails_enabled=False,
        )


def test_production_requires_conversation_signing_and_rate_limits():
    with pytest.raises(ValidationError, match="CONVERSATION_SIGNING_SECRET"):
        Settings(app_env="production", booking_access_otp_secret="a" * 32)

    with pytest.raises(ValidationError, match="RATE_LIMITS_ENABLED"):
        Settings(
            app_env="production",
            booking_access_otp_secret="a" * 32,
            conversation_signing_secret="b" * 32,
            rate_limits_enabled=False,
        )
