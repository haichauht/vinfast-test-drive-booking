import pytest


@pytest.mark.asyncio
async def test_chat_accepts_minimum_length_message(client):
    response = await client.post("/api/v1/chat", json={"message": "a"})

    assert response.status_code == 200
    assert "response" in response.json()


@pytest.mark.asyncio
async def test_chat_accepts_maximum_length_message(client):
    response = await client.post("/api/v1/chat", json={"message": "a" * 5000})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_rejects_message_over_maximum_length(client):
    response = await client.post("/api/v1/chat", json={"message": "a" * 5001})

    assert response.status_code == 422
