import re

def normalize_whitespace(text: str) -> str:
    text = (text or "").strip()
    # заменяем любые подряд идущие пробельные символы на 1 пробел
    text = re.sub(r"\s+", " ", text)
    return text