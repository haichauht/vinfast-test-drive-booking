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

LOOKUP_KEYWORDS: list[str] = [
    "tra cứu lịch",
    "tra cuu lich",
    "xem lịch đã đặt",
    "xem lich da dat",
    "tìm lịch đã đặt",
    "tim lich da dat",
    "booking của tôi",
    "booking cua toi",
]

