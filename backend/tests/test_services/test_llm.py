from types import SimpleNamespace

from src.services import llm


def test_build_llm_returns_none_when_no_provider_key(monkeypatch):
    monkeypatch.setattr(
        llm,
        "get_settings",
        lambda: SimpleNamespace(openrouter_api_key="", openai_api_key=""),
    )

    assert llm._build_llm("gpt-4o-mini", 0.7) is None
