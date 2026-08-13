import pytest


@pytest.mark.asyncio
# test case of Chau + kiểm tra health endpoint báo backend đang hoạt động
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
# test case of Chau + kiểm tra chat từ chối message rỗng bằng validation 422
async def test_chat_empty_message(client):
    response = await client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
# test case of Chau + kiểm tra status endpoint trả trạng thái agent sẵn sàng
async def test_agent_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/dashboard"),
        ("POST", "/api/v1/admin/import/showrooms"),
        ("POST", "/api/v1/admin/import/eval-dataset"),
    ],
)
async def test_admin_routes_are_not_publicly_exposed(client, method, path):
    response = await client.request(method, path, json={})
    assert response.status_code == 404
