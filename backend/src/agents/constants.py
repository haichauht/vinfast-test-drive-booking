"""Shared constants used across multiple agent nodes.

Centralizing keyword lists here prevents duplication (DRY principle)
between classifier_node.py and sensitive_policy_node.py.
"""

# Keywords that bypass the LLM classifier and route directly to sensitive_policy_node
SOVEREIGNTY_KEYWORDS: list[str] = [
    "hoàng sa",
    "trường sa",
    "biển đông",
    "paracel",
    "spratly",
]

OUT_OF_SCOPE_KEYWORDS: list[str] = [
    "viết code",
    "lập trình",
    "python",
    "javascript",
    "code python",
    "viết script",
    "giải toán",
]
