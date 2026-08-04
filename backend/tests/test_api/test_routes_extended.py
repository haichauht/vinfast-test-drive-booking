import pytest


# test case of Chau + kiểm tra echo endpoint trả text mặc định và timestamp
@pytest.mark.asyncio
async def test_echo_default_value(client):
    response = await client.get("/api/v1/echo")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["echo"] == "Hello"
    assert data["time"]


# test case of Chau + kiểm tra echo endpoint trả đúng text do người dùng truyền
@pytest.mark.asyncio
async def test_echo_custom_value(client):
    response = await client.get("/api/v1/echo", params={"text": "VinFast"})

    assert response.status_code == 200
    assert response.json()["echo"] == "VinFast"


# test case of Chau + kiểm tra chat chấp nhận message có một ký tự
@pytest.mark.asyncio
async def test_chat_accepts_minimum_length_message(client):
    response = await client.post("/api/v1/chat", json={"message": "a"})

    assert response.status_code == 200
    assert "response" in response.json()


# test case of Chau + kiểm tra chat chấp nhận message đúng giới hạn năm nghìn ký tự
@pytest.mark.asyncio
async def test_chat_accepts_maximum_length_message(client):
    response = await client.post("/api/v1/chat", json={"message": "a" * 5000})

    assert response.status_code == 200


# test case of Chau + kiểm tra chat từ chối message vượt quá năm nghìn ký tự
@pytest.mark.asyncio
async def test_chat_rejects_message_over_maximum_length(client):
    response = await client.post("/api/v1/chat", json={"message": "a" * 5001})

    assert response.status_code == 422


# test case of Chau + kiểm tra demo action từ chối action name không tồn tại
@pytest.mark.asyncio
async def test_demo_action_rejects_unknown_action(client):
    response = await client.post("/api/v1/demo/action", json={"action": "unknown-action", "payload": {}})

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown demo action"


# test case of Chau + kiểm tra client log từ chối message rỗng
@pytest.mark.asyncio
async def test_client_log_rejects_empty_message(client):
    response = await client.post("/api/v1/client-log", json={"level": "info", "message": "", "context": {}})

    assert response.status_code == 422


# test case of Chau + kiểm tra dashboard từ chối limit không phải số nguyên
@pytest.mark.asyncio
async def test_dashboard_rejects_non_integer_limit(client):
    response = await client.get("/api/v1/dashboard", params={"limit": "abc"})

    assert response.status_code == 422
