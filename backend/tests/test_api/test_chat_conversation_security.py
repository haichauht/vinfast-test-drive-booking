import importlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

routes_module = importlib.import_module("src.api.routes")


def _mock_agent(monkeypatch, result=None, exception=None):
    mocked = MagicMock()
    if exception is not None:
        mocked.ainvoke = AsyncMock(side_effect=exception)
    else:
        mocked.ainvoke = AsyncMock(return_value=result or {"response": "Agent response", "analysis": "trace"})
    monkeypatch.setattr(routes_module, "agent", mocked)
    return mocked


# test case of Chau + kiểm tra API tự sinh conversation id hợp lệ và truyền đúng vào LangGraph thread
@pytest.mark.asyncio
async def test_chat_generates_conversation_id_and_uses_it_as_thread_id(client, monkeypatch):
    mocked = _mock_agent(monkeypatch)

    response = await client.post("/api/v1/chat", json={"message": "VF8 range"})

    assert response.status_code == 200
    payload = response.json()
    uuid.UUID(payload["conversation_id"])
    (state,) = mocked.ainvoke.await_args.args
    assert state == {"query": "VF8 range"}
    assert mocked.ainvoke.await_args.kwargs["config"] == {"configurable": {"thread_id": payload["conversation_id"]}}


# test case of Chau + kiểm tra API giữ nguyên conversation id để tiếp tục đúng phiên hội thoại
@pytest.mark.asyncio
async def test_chat_reuses_client_conversation_id(client, monkeypatch):
    mocked = _mock_agent(monkeypatch, {"response": "Continued", "analysis": ""})
    conversation_id = "chau-conversation-1"

    response = await client.post(
        "/api/v1/chat",
        json={"message": "Continue booking", "conversation_id": conversation_id},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == conversation_id
    assert mocked.ainvoke.await_args.kwargs["config"]["configurable"]["thread_id"] == conversation_id


# test case of Chau + kiểm tra message trắng bị từ chối thay vì tốn một lượt gọi agent
@pytest.mark.asyncio
async def test_chat_rejects_whitespace_only_message(client, monkeypatch):
    mocked = _mock_agent(monkeypatch)

    response = await client.post("/api/v1/chat", json={"message": "   \n\t"})

    assert response.status_code == 422
    mocked.ainvoke.assert_not_awaited()


# test case of Chau + kiểm tra conversation id quá dài bị chặn để bảo vệ memory checkpoint key
@pytest.mark.asyncio
async def test_chat_rejects_oversized_conversation_id(client, monkeypatch):
    mocked = _mock_agent(monkeypatch)

    response = await client.post(
        "/api/v1/chat",
        json={"message": "Hello", "conversation_id": "x" * 10000},
    )

    assert response.status_code == 422
    mocked.ainvoke.assert_not_awaited()


# test case of Chau + kiểm tra lỗi nội bộ agent không làm lộ secret hoặc chi tiết hạ tầng
@pytest.mark.asyncio
async def test_chat_does_not_expose_internal_exception_details(client, monkeypatch):
    _mock_agent(
        monkeypatch,
        exception=RuntimeError("database password=super-secret; provider host=internal.local"),
    )

    response = await client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 500
    body = response.text.lower()
    assert "super-secret" not in body
    assert "internal.local" not in body
