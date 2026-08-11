import pytest
from pydantic import ValidationError

from src.config import Settings


def test_production_requires_a_strong_otp_secret():
    with pytest.raises(ValidationError, match="BOOKING_ACCESS_OTP_SECRET"):
        Settings(app_env="production", booking_access_otp_secret="too-short")

    settings = Settings(app_env="production", booking_access_otp_secret="a" * 32)

    assert settings.booking_access_otp_secret == "a" * 32
