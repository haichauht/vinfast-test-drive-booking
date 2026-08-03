import os

# Override DATABASE_URL to use SQLite for tests before importing the app
os.environ["DATABASE_URL"] = "sqlite:///./data/test.db"

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


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock ChatOpenAI globally to avoid real API calls and import order issues."""
    from langchain_core.messages import AIMessage

    mock_instance = MagicMock()
    mock_response = AIMessage(content="Mocked LLM response")

    # Mock basic invoke/ainvoke
    mock_instance.ainvoke = AsyncMock(return_value=mock_response)

    # Mock bind_tools to return the mock instance so we can chain ainvoke on it
    mock_instance.bind_tools = MagicMock(return_value=mock_instance)

    # Mock with_structured_output for classifier_node
    mock_structured = MagicMock()
    from src.agents.nodes.classifier_node import RouteSchema

    async def mock_classify(prompt, **kwargs):
        prompt_lower = prompt.lower()
        query_part = prompt_lower.split("user query:")[-1] if "user query:" in prompt_lower else prompt_lower
        # Remove punctuation to ensure clean word splitting
        query_clean = "".join(c if c.isalnum() or c.isspace() else " " for c in query_part)
        words = query_clean.split()
        if any(kw in words for kw in ["chào", "hello", "hi"]):
            return RouteSchema(intent="general", sub_intent="small_talk")
        elif any(kw in words or kw in query_part for kw in ["vf8", "sạc", "km", "thông số", "giá"]):
            return RouteSchema(intent="domain", sub_intent="vehicle_info")
        return RouteSchema(intent="domain", sub_intent="booking")

    mock_structured.ainvoke = AsyncMock(side_effect=mock_classify)
    mock_instance.with_structured_output = MagicMock(return_value=mock_structured)

    with patch("src.services.llm.ChatOpenAI", return_value=mock_instance):
        yield mock_instance
