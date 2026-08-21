import json

from langchain_core.tools import tool
from src.dependencies import knowledge_service


@tool
def search_knowledge(
    query: str,
    model_code: str = "",
    topics: list[str] | None = None,
    market: str = "VN",
    trim: str = "",
    model_year: str = "",
) -> str:
    """Search the provenance-aware post-booking knowledge base.

    Args:
        query: The user's knowledge question.
        model_code: Exact vehicle model when known, for example ``VF 6``.
        topics: Optional knowledge topic filters.
        market: Market scope; defaults to Vietnam.
        trim: Exact vehicle trim when known.
        model_year: Exact four-digit model year when known.

    Returns:
        JSON containing scoped facts, citations, review status, and live-data boundaries.
    """
    return json.dumps(
        knowledge_service.search(
            query,
            model_code=model_code,
            topics=topics,
            market=market,
            trim=trim,
            model_year=model_year,
        ),
        ensure_ascii=False,
    )
