from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.api import routes as routes_module


@pytest.mark.asyncio
async def test_floating_demo_is_hidden_when_server_capability_is_disabled(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="development", floating_demo_enabled=False),
    )

    response = await client.get("/api/v1/floating-demo/capabilities")

    assert response.status_code == 200
    assert response.json()["enabled"] is False

    denied = await client.post(
        "/api/v1/floating-demo/confirm",
        json={"booking_id": "booking-1", "expected_version": 2, "ui_action_id": "demo-confirm-1"},
    )
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_floating_demo_confirms_only_when_enabled_outside_production(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="development", floating_demo_enabled=True),
    )
    confirm = MagicMock(return_value={"booking_id": "booking-1", "booking_code": "VF260824ABC", "status": "confirmed"})
    monkeypatch.setattr(routes_module.booking_service, "confirm_booking", confirm)

    response = await client.post(
        "/api/v1/floating-demo/confirm",
        json={"booking_id": "booking-1", "expected_version": 2, "ui_action_id": "demo-confirm-1"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["booking_code"] == "VF260824ABC"
    confirm.assert_called_once_with("booking-1", "demo-confirm-1", 2)


@pytest.mark.asyncio
async def test_floating_demo_hold_marks_the_booking_source(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="development", floating_demo_enabled=True),
    )
    hold = MagicMock(return_value={"booking_id": "booking-1", "status": "held", "version": 1})
    monkeypatch.setattr(routes_module.booking_service, "hold_slot", hold)

    response = await client.post(
        "/api/v1/floating-demo/hold",
        json={"slot_id": "slot-1", "ui_action_id": "demo-hold-1"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["booking_id"] == "booking-1"
    hold.assert_called_once_with(
        "slot-1",
        "demo-hold-1",
        source_channel="floating_demo",
        _operation="floating_demo_hold",
    )


@pytest.mark.asyncio
async def test_floating_demo_saves_the_self_booking_persona_directly(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="development", floating_demo_enabled=True),
    )
    update = MagicMock(return_value={"booking_id": "booking-1", "version": 2, "status": "held"})
    monkeypatch.setattr(routes_module.booking_service, "update_booking_draft", update)

    response = await client.post(
        "/api/v1/floating-demo/draft",
        json={
            "booking_id": "booking-1",
            "expected_version": 1,
            "full_name": "Nguyễn Hải Đăng",
            "phone": "0901000000",
            "email": "demo.booking@example.test",
            "has_license": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["version"] == 2
    update.assert_called_once_with(
        "booking-1",
        booker_patch={"full_name": "Nguyễn Hải Đăng", "phone": "0901000000", "email": "demo.booking@example.test"},
        driver_same_as_booker=True,
        license_patch={"has_driving_license": True},
        expected_version=1,
    )


@pytest.mark.asyncio
async def test_floating_demo_is_unavailable_in_production_even_when_enabled(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="production", floating_demo_enabled=True),
    )

    response = await client.post(
        "/api/v1/floating-demo/confirm",
        json={"booking_id": "booking-1", "expected_version": 2, "ui_action_id": "demo-confirm-1"},
    )

    assert response.status_code == 404
