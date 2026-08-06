from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.config import get_settings


def _build_llm(model: str, temperature: float) -> ChatOpenAI:
    settings = get_settings()
    if settings.openrouter_api_key:
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(settings.openrouter_api_key),
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
        )
    if settings.openai_api_key:
        return ChatOpenAI(
            model=model.removeprefix("openai/"),
            api_key=SecretStr(settings.openai_api_key),
            temperature=temperature,
        )
    # Keep construction lazy-safe so non-Agent endpoints and deterministic UI
    # actions remain available without an LLM key. The model call itself will be
    # caught by the Agent node and converted to a user-safe response.
    return ChatOpenAI(
        model=model.removeprefix("openai/"),
        api_key=SecretStr("not-configured"),
        temperature=temperature,
    )


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return _build_llm(settings.model_name, settings.llm_temperature)


def get_classifier_llm() -> ChatOpenAI:
    settings = get_settings()
    return _build_llm(settings.classifier_model_name or settings.model_name, 0.0)
