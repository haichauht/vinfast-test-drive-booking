from src.security.rate_limit import route_class_for_path


def test_all_public_booking_action_aliases_use_the_canonical_rate_limiter():
    assert route_class_for_path("/api/v1/chat") == "chat"
    assert route_class_for_path("/api/v1/demo/action") == "demo_action"
    assert route_class_for_path("/api/v1/test-drive/actions") == "demo_action"


def test_unrelated_routes_are_not_accidentally_classified():
    assert route_class_for_path("/health") is None
