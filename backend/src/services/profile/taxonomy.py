ALLOWED_CATEGORIES = {
    "fact", "usage", "experience", "interest", "concern", "test_drive_goal",
    "conversation_preference", "likely_intent", "custom_intent",
}


def normalize_key(value: str) -> str:
    normalized = "_".join(value.casefold().strip().replace("-", " ").split())
    return "".join(char for char in normalized if char.isalnum() or char == "_")[:100]

