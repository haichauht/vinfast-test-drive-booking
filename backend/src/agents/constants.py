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

BOOKING_MUTATION_KEYWORDS: list[str] = [
    "đặt lịch", "tìm showroom", "tìm lịch", "giữ chỗ", "xác nhận đặt", "tra cứu lịch",
    "đổi lịch", "dời lịch", "hủy lịch", "huỷ lịch", "sửa lịch", "mã otp", "xác thực otp",
]

ADVISORY_KEYWORDS: list[str] = [
    "cần mang gì", "chuẩn bị", "nên thử", "nên kiểm tra", "nên hỏi", "lái thử",
    "pin", "sạc", "range", "quãng đường", "adas", "camera", "an toàn", "gia đình",
    "ghế trẻ em", "đỗ xe", "đậu xe", "hầm", "chi phí sử dụng", "xe điện",
]
