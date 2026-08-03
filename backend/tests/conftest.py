from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm():
    """Mock LLM injected into the app to avoid real OpenAI/OpenRouter API calls during tests.

    Usage in test:
        async def test_something(client, mock_llm):
            response = await client.post("/api/v1/chat", json={"message": "hello"})
            assert response.status_code == 200
    """
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mocked LLM response"
    mock.ainvoke = AsyncMock(return_value=mock_response)
    mock.with_structured_output = MagicMock(return_value=mock)

    # Patch both LLM factory functions so no real API calls are made
    with patch("src.services.llm.get_llm", return_value=mock), \
         patch("src.services.llm.get_classifier_llm", return_value=mock):
        yield mock
