from langchain_openai import ChatOpenAI

from src.config import get_settings


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    if settings.openrouter_api_key:
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=settings.llm_temperature,
        )
    return ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
    )


def get_classifier_llm() -> ChatOpenAI:
    settings = get_settings()
    if settings.openrouter_api_key:
        return ChatOpenAI(
            model=settings.classifier_model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.0,  # Classifier luôn cần temperature = 0 để phân loại chính xác
        )
    return ChatOpenAI(
        model=settings.classifier_model_name,
        api_key=settings.openai_api_key,
        temperature=0.0,
    )
