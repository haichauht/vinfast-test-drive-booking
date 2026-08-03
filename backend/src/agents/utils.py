from pathlib import Path

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"


def get_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are Vini, the VinFast Test Drive Virtual Assistant."
