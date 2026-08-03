import pytest
from src.agents.graph import agent


def _cfg(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


@pytest.mark.asyncio
async def test_agent_basic_flow():
    result = await agent.ainvoke({"query": "Hello"}, config=_cfg("test-basic"))
    assert "response" in result


@pytest.mark.asyncio
async def test_agent_state_structure():
    result = await agent.ainvoke({"query": "Test query"}, config=_cfg("test-state"))
    assert isinstance(result, dict)
    assert "query" in result
