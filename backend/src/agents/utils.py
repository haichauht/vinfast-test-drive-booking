from pathlib import Path

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"


from datetime import datetime

def get_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
            content = f.read()
            WEEKDAYS_VI = {
                0: "Thứ 2",
                1: "Thứ 3",
                2: "Thứ 4",
                3: "Thứ 5",
                4: "Thứ 6",
                5: "Thứ 7",
                6: "Chủ nhật"
            }
            now = datetime.now()
            weekday_str = WEEKDAYS_VI[now.weekday()]
            date_str = now.strftime("%Y-%m-%d %H:%M:%S")
            time_context = f"\n\n--- CURRENT TIME CONTEXT ---\nToday is: {weekday_str}, {date_str} (Vietnam Local Time)"
            return content + time_context
    except Exception:
        return "You are Vini, the VinFast Test Drive Virtual Assistant."
