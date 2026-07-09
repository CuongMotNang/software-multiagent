"""Helper dùng chung khi parse JSON output từ LLM (dễ lặp lỗi bọc ```json)."""


def strip_code_fence(text: str) -> str:
    """LLM đôi khi vẫn bọc ```json...``` dù prompt đã cấm — bóc ra trước khi parse."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
        elif "```" in t:
            t = t.rsplit("```", 1)[0]
    return t.strip()
