import re
import html
import json


def esc(text):
    return html.escape(str(text)).replace("\n", "<br>")


def sanitize_title(title: str) -> str:
    title = re.sub(r"\s+", " ", str(title)).strip()
    return title[:40] if title else "New Chat"


def detect_lang_instruction(text: str) -> str:
    t = text.lower().strip()

    patterns = [
        r"answer in ([a-zA-Z\s]+)",
        r"reply in ([a-zA-Z\s]+)",
        r"respond in ([a-zA-Z\s]+)",
        r"write in ([a-zA-Z\s]+)",
        r"explain in ([a-zA-Z\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            lang = match.group(1).strip(" .,!?:;")
            if lang:
                return f"Answer in {lang}."

    return "Answer in English."


def generate_short_title_prompt(user_message: str) -> str:
    return f"""
Generate a short chat title for this message.

Rules:
- 2 to 4 words
- No quotes
- No punctuation unless necessary
- Clean and natural

Message:
{user_message}
"""


def parse_json_array(text: str):
    if not text:
        return []

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    code_block_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        try:
            data = json.loads(code_block_match.group(1))
            if isinstance(data, list):
                return data
        except Exception:
            pass

    array_match = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
    if array_match:
        try:
            data = json.loads(array_match.group(0))
            if isinstance(data, list):
                return data
        except Exception:
            pass

    return []