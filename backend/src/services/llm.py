from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.config import get_settings


def _build_llm(model: str, temperature: float) -> ChatOpenAI | None:
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
    # Deterministic endpoints remain available without an LLM key. Returning
    # None makes that state explicit so Agent nodes can choose a safe fallback
    # without constructing a provider client with a fake credential.
    return None


def get_llm() -> ChatOpenAI | None:
    settings = get_settings()
    return _build_llm(settings.model_name, settings.llm_temperature)


def get_classifier_llm() -> ChatOpenAI | None:
    settings = get_settings()
    return _build_llm(settings.classifier_model_name or settings.model_name, 0.0)
