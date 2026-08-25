from types import SimpleNamespace

import pytest
from src.api import routes as routes_module


@pytest.mark.asyncio
async def test_floating_demo_capability_is_disabled_when_server_flag_is_off(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="development", floating_demo_enabled=False),
    )

    response = await client.get("/api/v1/floating-demo/capabilities")

    assert response.status_code == 200
    assert response.json()["enabled"] is False


@pytest.mark.asyncio
async def test_floating_demo_capability_is_disabled_in_production(client, monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "get_settings",
        lambda: SimpleNamespace(app_env="production", floating_demo_enabled=True),
    )

    response = await client.get("/api/v1/floating-demo/capabilities")

    assert response.status_code == 200
    assert response.json()["enabled"] is False


@pytest.mark.asyncio
async def test_removed_demo_confirmation_endpoint_cannot_bypass_otp(client):
    response = await client.post(
        "/api/v1/floating-demo/confirm",
        json={"booking_id": "booking-1", "expected_version": 1, "ui_action_id": "demo-confirm-1"},
    )

    assert response.status_code == 404
