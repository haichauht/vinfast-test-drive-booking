from src.config import Settings
from src.security.client_identity import ClientIdentity
from src.security.rate_limit import rules_for_route


def test_chat_uses_minute_and_hour_limits_for_session_and_ip():
    settings = Settings(
        rate_limit_chat_per_session_per_minute=10,
        rate_limit_chat_per_session_per_hour=120,
        rate_limit_chat_per_ip_per_minute=60,
        rate_limit_chat_per_ip_per_hour=600,
    )
    identity = ClientIdentity(session_id="session-1", client_ip="127.0.0.1")

    rules = rules_for_route("chat", identity, settings)

    assert [(rule.key, rule.limit, rule.window_seconds) for rule in rules] == [
        ("chat:session:minute:session-1", 10, 60),
        ("chat:session:hour:session-1", 120, 3_600),
        ("chat:ip:minute:127.0.0.1", 60, 60),
        ("chat:ip:hour:127.0.0.1", 600, 3_600),
    ]


def test_demo_action_uses_minute_and_hour_limits_for_session_and_ip():
    settings = Settings(
        rate_limit_demo_action_per_session_per_minute=30,
        rate_limit_demo_action_per_session_per_hour=300,
        rate_limit_demo_action_per_ip_per_minute=120,
        rate_limit_demo_action_per_ip_per_hour=1_200,
    )
    identity = ClientIdentity(session_id="session-1", client_ip="127.0.0.1")

    rules = rules_for_route("demo_action", identity, settings)

    assert [(rule.key, rule.limit, rule.window_seconds) for rule in rules] == [
        ("demo_action:session:minute:session-1", 30, 60),
        ("demo_action:session:hour:session-1", 300, 3_600),
        ("demo_action:ip:minute:127.0.0.1", 120, 60),
        ("demo_action:ip:hour:127.0.0.1", 1_200, 3_600),
    ]


def test_default_otp_request_limit_is_ten_per_contact_per_hour(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR", raising=False)

    assert Settings(_env_file=None).rate_limit_otp_request_per_contact_per_hour == 10
